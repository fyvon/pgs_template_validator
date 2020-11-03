import re, csv

from openpyxl import load_workbook
import urllib.request
from urllib.error import HTTPError
from io import BytesIO

from validator.demographic import Demographic
from validator.efotrait import EFOTrait
from validator.metric import Metric
from validator.performance import PerformanceMetric
from validator.publication import Publication
from validator.sample import Sample
from validator.score import Score

# Needed for parsing confidence intervals
insquarebrackets = re.compile('\\[([^)]+)\\]')
interval_format = '^\d+.?\d*\s\-\s\d+.?\d*$'
inparentheses = re.compile('\((.*)\)')

template_columns_schema_file = './templates/TemplateColumns2Models_v5.xlsx'

class PGSMetadataValidator():

    def __init__(self, filepath, is_remote):
        self.filepath = filepath
        self.is_remote = is_remote
        self.parsed_publication = None
        self.parsed_scores = {}
        self.parsed_efotraits = {}
        self.parsed_samples_scores = []
        self.parsed_samples_testing = []
        self.parsed_performances = {}
        self.parsed_samplesets = []
        self.cohorts_list = []
        self.template_columns_schema_file = './templates/TemplateColumns2Models_v5.xlsx'
        self.table_mapschema = {}
        self.loc_localGWAS = './local_GWASCatalog/'
        self.report = { 'error': {}, 'warning': {} }
        self.spreadsheet_names = {}


    def load_workbook_from_url(self):
        url = self.filepath
        try:
            with urllib.request.urlopen(str(url)) as url:
                stream = url.read()
                workbook = load_workbook(filename=BytesIO(stream))
                return workbook
        except urllib.error.HTTPError as e:
            if e.code == 404:
                msg = 'The upload of the file failed'
            else:
                msg = e.reason
            self.report_error('General',None,'The upload of the file failed')
            return None


    def parse_spreadsheets(self):
        '''ReadCuration takes as input the location of a study metadata file'''

        self.parse_template_schema()

        loaded_spreadsheets = False
        loc_excel = self.filepath
        if loc_excel != None:
            print("REMOTE: "+str(self.is_remote))
            if self.is_remote:
                workbook = self.load_workbook_from_url()
            else:
                workbook = load_workbook(loc_excel, data_only=True)

            if workbook:
                loaded_spreadsheets = True

                print(str(workbook.sheetnames))

                self.workbook_publication = workbook[self.spreadsheet_names['Publication']]
                print(str(self.workbook_publication))

                #self.table_publication = pd.read_excel(loc_excel, sheet_name='Publication Information', header=0, index_col=0)

                self.workbook_scores = workbook[self.spreadsheet_names['Score']]
                #self.table_scores = pd.read_excel(loc_excel, sheet_name='Score(s)', header=[0, 1], index_col=0)

                self.workbook_samples = workbook[self.spreadsheet_names['Sample']]
                #self.table_samples = pd.read_excel(loc_excel, sheet_name='Sample Descriptions', header=0)

                # Parse to separate tables
                #self.table_samples_scores = self.table_samples[self.table_samples.iloc[:,1] != 'Testing ']
                #self.table_samples_scores.set_index(list(self.table_samples_scores.columns[[0, 1]]), inplace = True)
                #self.table_samples_testing = self.table_samples[self.table_samples.iloc[:, 1] == 'Testing ']
                #self.table_samples_testing.set_index(list(self.table_samples_testing.columns[[2]]), inplace=True)

                self.workbook_performances = workbook[self.spreadsheet_names['Performance']]
                #self.table_performances = pd.read_excel(loc_excel, sheet_name='Performance Metrics', header=[0,1], index_col=[0, 1])

                self.workbook_cohorts = workbook[self.spreadsheet_names['Cohort']]
                #self.table_cohorts = pd.read_excel(loc_excel, sheet_name='Cohort Refr.', header=0, index_col=0)
        return loaded_spreadsheets


    def parse_template_schema(self):
        schema_workbook = load_workbook(self.template_columns_schema_file)
        curation_sheet = schema_workbook["Curation"]
        schema_columns = get_column_name_index(curation_sheet)
        for row_cell in curation_sheet.iter_rows(min_row=2, values_only=True):
            data = {}
            sheet_name = row_cell[0]
            column_name = row_cell[schema_columns['Column']]
            model_name = row_cell[schema_columns['Model']]
            field_name = row_cell[schema_columns['Field']]
            if not sheet_name in self.table_mapschema:
                self.table_mapschema[sheet_name] = {}
            self.table_mapschema[sheet_name][column_name] = field_name

            if not model_name in self.spreadsheet_names:
                self.spreadsheet_names[model_name] = sheet_name


    def parse_publication(self):
        spread_sheet_name = self.spreadsheet_names['Publication']
        col_names = get_column_name_index(self.workbook_publication)
        c_doi = ''
        c_PMID = ''
        row_start = 2
        row_id = row_start
        for pinfo in self.workbook_publication.iter_rows(min_row=row_start, max_row=row_start, values_only=True):
            c_doi = pinfo[col_names['doi']]
            c_doi = self.check_and_remove_whitespaces(spread_sheet_name, None, 'doi', c_doi)
            c_PMID = pinfo[1]
            c_PMID = self.check_and_remove_whitespaces(spread_sheet_name, None, 'PubMed ID', c_PMID)

        # PubMed ID
        if c_PMID != '':
            c_PMID = str(c_PMID)
            if not re.search('^\d+$',c_PMID):
                self.report_error(spread_sheet_name,row_id,"PubMed ID format should be ony numeric (found: "+c_PMID+")")

        publication = Publication(c_doi, c_PMID)
        publication.populate_from_eupmc()
        publication_check_report = publication.check_data()
        self.add_check_report(spread_sheet_name, row_id, publication_check_report)


    def parse_scores(self):
        spread_sheet_name = self.spreadsheet_names['Score']
        current_schema = self.table_mapschema[spread_sheet_name]
        col_names = get_column_name_index(self.workbook_scores, row_index=2)

        row_start = 3
        for row_id, score_info in enumerate(self.workbook_scores.iter_rows(min_row=row_start, max_row=self.workbook_scores.max_row, values_only=True), start=row_start):
            score_name = score_info[0]
            if not score_name or score_name == '':
                break
            parsed_score = { 'name' : score_name }
            for col_name in col_names:
                val = score_info[col_names[col_name]]
                val = self.check_and_remove_whitespaces(spread_sheet_name, row_id, col_name, val)
                if (col_name in current_schema) and (val != ''):
                    field = current_schema[col_name]
                    if field == 'trait_efo':
                        efo_list = val.split(',')
                        parsed_score[field] = efo_list
                    else:
                        parsed_score[field] = val

            for trait_efo_id in parsed_score['trait_efo']:
                if not trait_efo_id in self.parsed_efotraits:
                    efo_trait = EFOTrait(trait_efo_id)
                    efo_trait.populate_from_efo()
                    if efo_trait.label:
                        self.parsed_efotraits[trait_efo_id] = efo_trait
                    else:
                        self.report_error(spread_sheet_name,row_id,"Can't find a corresponding entry in EFO for '"+trait_efo_id+"'")

            if not 'trait_additional' in parsed_score:
                parsed_score['trait_additional'] = None

            score = Score(
                parsed_score['name'],
                parsed_score['trait_reported'],
                parsed_score['trait_efo'],
                parsed_score['method_name'],
                parsed_score['method_params'],
                parsed_score['variants_number'],
                parsed_score['variants_interactions'],
                parsed_score['variants_genomebuild'],
                parsed_score['trait_additional']
            )
            score_check_report = score.check_data()
            self.add_check_report(spread_sheet_name, row_id, score_check_report)

            self.parsed_scores[score_name] = score


    def parse_cohorts(self):
        spread_sheet_name = self.spreadsheet_names['Cohort']
        current_schema = self.table_mapschema[spread_sheet_name]
        row_start = 2
        for cohort_info in self.workbook_cohorts.iter_rows(min_row=row_start, max_row=self.workbook_cohorts.max_row, values_only=True):
            cohort_id = cohort_info[0].upper()
            cohort_id = cohort_id.strip()
            if not cohort_id in self.cohorts_list:
                self.cohorts_list.append(cohort_id)


    def cohort_to_list(self, cstring, row_id, spread_sheet_name):
        #cohort_df = self.table_cohorts
        clist = set()
        for cname in cstring.split(','):
            cname = cname.strip().upper()
            if not cname in self.cohorts_list:
                self.report_warning(spread_sheet_name,row_id,"Can't find a corresponding cohort ID in the Cohort spreadsheet for '"+str(cname)+"'")
            clist.add(cname)

        return list(clist)


    def parse_performances(self):
        spread_sheet_name = self.spreadsheet_names['Performance']
        current_schema = self.table_mapschema[spread_sheet_name]
        col_names = get_column_name_index(self.workbook_performances, row_index=2)

        score_names_list = self.parsed_scores.keys()

        row_start = 3
        for row_id, performance_info in enumerate(self.workbook_performances.iter_rows(min_row=row_start, max_row=self.workbook_performances.max_row, values_only=True), start=row_start):
            score_name = performance_info[0]
            score_name = self.check_and_remove_whitespaces(spread_sheet_name, row_id, 'Score Name/ID', score_name)
            sampleset  = performance_info[1]
            sampleset = self.check_and_remove_whitespaces(spread_sheet_name, row_id, 'Sample Set ID', sampleset)
            phenotyping_reported = performance_info[2]
            phenotyping_reported = self.check_and_remove_whitespaces(spread_sheet_name, row_id, 'Predicted Trait Name', phenotyping_reported)

            if not score_name or score_name == '':
                break

            parsed_performance = {
                'score_name': score_name,
                'sampleset':  sampleset,
                'phenotyping_reported': phenotyping_reported,
                'metrics': []
            }
            if not sampleset in self.parsed_samplesets:
                self.parsed_samplesets.append(sampleset)

            if not score_name in score_names_list:
                self.report_error(spread_sheet_name,row_id,"Score name '"+score_name+"' from the Performance Metrics spreadsheet can't be found in the Score(s) spreadsheet!")

            #for col, val in performance_info.iteritems():
            for col_name in col_names:
                val = performance_info[col_names[col_name]]
                val = self.check_and_remove_whitespaces(spread_sheet_name, row_id, col_name, val)
                if (col_name in current_schema) and (val != '') and val:
                    field = current_schema[col_name]
                    if field.startswith('metric'):
                        if ';' in str(val):
                            try:
                                for x in val.split(';'):
                                    parsed_performance['metrics'].append(self.str2metric(field, x, row_id, spread_sheet_name, self.workbook_performances))
                            except:
                                error_msg = "Error parsing the metric value '"+str(val)+"'"
                                self.report_error(spread_sheet_name,row_id,error_msg)
                        else:
                            parsed_performance['metrics'].append(self.str2metric(field, val, row_id, spread_sheet_name, self.workbook_performances))
                    else:
                        parsed_performance[field] = val

            if len(parsed_performance['metrics']) > 0:

                performance = PerformanceMetric(
                    parsed_performance['score_name'],
                    parsed_performance['sampleset'],
                    parsed_performance['phenotyping_reported'],
                    parsed_performance['metrics']
                )
                if 'covariates' in parsed_performance:
                    performance.covariates = parsed_performance['covariates']
                if 'performance_comments' in parsed_performance:
                    performance.performance_comments = parsed_performance['performance_comments']

                performance_check_report = performance.check_data()
                self.add_check_report(spread_sheet_name, row_id, performance_check_report)

                #self.parsed_scores[score_name] = score
                performance_id = parsed_performance['score_name']+'__'+parsed_performance['sampleset']
                self.parsed_performances[performance_id] = performance


    def parse_samples(self):
        spread_sheet_name = self.spreadsheet_names['Sample']
        current_schema = self.table_mapschema[spread_sheet_name]
        col_names = get_column_name_index(self.workbook_samples)

        samples_scores = {}
        samples_testing = {}
        # Extract data for training (GWAS + Score Development) sample
        row_start = 2
        for row_id, sample_info in enumerate(self.workbook_samples.iter_rows(min_row=row_start, max_row=self.workbook_samples.max_row, values_only=True), start=row_start):

            score_name = sample_info[0]
            score_name = self.check_and_remove_whitespaces(spread_sheet_name, row_id, 'Associated Score Name(s)', score_name)
            sample_study_type = sample_info[1]
            # Corresponds to the end of the data
            if not sample_study_type or sample_study_type == '':
                break

            sample_study_type = self.check_and_remove_whitespaces(spread_sheet_name, row_id, 'Study Stage', sample_study_type)

            if re.search('Testing',sample_study_type):
                samples_testing[row_id] = sample_info
            else:
                if not score_name or score_name == '':
                    self.report_error(spread_sheet_name, row_id, "The column 'Associated Score Name(s)' is empty.")
                    break
                samples_scores[row_id] = sample_info

        if len(samples_testing.keys()) == 0:
            self.report_error(spread_sheet_name, None, "There are no 'Testing' sample entries for this study.")

        self.parse_samples_scores(spread_sheet_name, current_schema, samples_scores, col_names)
        self.parse_samples_testing(spread_sheet_name, current_schema, samples_testing, col_names)


    def parse_samples_scores(self, spread_sheet_name, current_schema, samples_scores, col_names):

        # Parse GWAS data
        gwas_samples = load_GWAScatalog(self.loc_localGWAS)

        samples = {}
        for row_id, sample_info in samples_scores.items():
            sample_remapped = {}
            for col_name in col_names:
                val = sample_info[col_names[col_name]]
                val = self.check_and_remove_whitespaces(spread_sheet_name, row_id, col_name, val)
                if (col_name in current_schema) and (val != '') and val:
                    field = current_schema[col_name]
                    if field == 'cohorts':
                        val = self.cohort_to_list(val, row_id,spread_sheet_name)
                    elif field in ['sample_age', 'followup_time']:
                        val = self.str2demographic(val, row_id, spread_sheet_name, self.workbook_samples)
                    sample_remapped[field] = val

            # Parse from GWAS Catalog
            if ('sample_number' not in sample_remapped.keys()):
                if ('source_GWAS_catalog' in sample_remapped) and (sample_remapped['source_GWAS_catalog'] in gwas_samples):
                    gwas_results = []
                    gwas_ss = gwas_samples[sample_remapped['source_GWAS_catalog']]
                    for gwas_study in gwas_ss:
                        c_sample = sample_remapped.copy()
                        for field, val in gwas_study.items():
                            c_sample[field] = val

                        if row_id in samples:
                            samples[row_id].append(c_sample)
                        else:
                            samples[row_id] = [c_sample]
            else:
                if row_id in samples:
                    samples[row_id].append(sample_remapped)
                else:
                    samples[row_id] = [sample_remapped]

        for row_id, sample_list in samples.items():
            for sample in sample_list:
                if re.search('^\=',str(sample['sample_number'])):
                    sample['sample_number'] = calculate_formula(self.workbook_samples,sample['sample_number'])
                sample_object = Sample(
                    int(float(sample['sample_number'])),
                    sample['ancestry_broad']
                )
                sample_object = complete_object(self.workbook_samples, sample_object,sample)
                sample_check_report = sample_object.check_data()
                self.add_check_report(spread_sheet_name, row_id, sample_check_report)

                self.parsed_samples_scores.append(sample_object)


    def parse_samples_testing(self, spread_sheet_name, current_schema, samples_testing, col_names):
        # Extract data Testing samples
        sample_sets_list = []

        for row_id, sample_info in samples_testing.items():
            sampleset = sample_info[2]
            sampleset = self.check_and_remove_whitespaces(spread_sheet_name, row_id, 'Sample Set ID', sampleset)

            if not sampleset in self.parsed_samplesets:
                    self.report_warning(spread_sheet_name, row_id, "The Sample Set ID '"+sampleset+"' is not present in the Performance Metrics spreadsheet")
            if not sampleset in sample_sets_list:
                    sample_sets_list.append(sampleset)

            sample_remapped = {}
            for col_name in col_names:
                val = sample_info[col_names[col_name]]
                val = self.check_and_remove_whitespaces(spread_sheet_name, row_id, col_name, val)
                #print("## "+col_name+": "+str(val))
                if (col_name in current_schema) and (val != '') and val:
                    field = current_schema[col_name]
                    if field == 'cohorts':
                        val = self.cohort_to_list(val, row_id, spread_sheet_name)
                    elif field in ['sample_age', 'followup_time']:
                        val = self.str2demographic(val, row_id, spread_sheet_name, self.workbook_samples)
                    sample_remapped[field] = val
                    #if val is not None:
                        #print(">> Field "+str(field)+": "+str(val))

            if re.search('^\=',str(sample_remapped['sample_number'])):
                sample_remapped['sample_number'] = calculate_formula(self.workbook_samples,sample_remapped['sample_number'])
            sample_object = Sample(
                int(sample_remapped['sample_number']),
                sample_remapped['ancestry_broad']
            )
            sample_object = complete_object(self.workbook_samples,sample_object,sample_remapped)
            sample_check_report = sample_object.check_data()
            self.add_check_report(spread_sheet_name, row_id, sample_check_report)

            self.parsed_samples_testing.append(sample_object)

        # Check if all the Sample Sets in the Performance Metrics spreadsheet have associated Samples
        for sampleset in self.parsed_samplesets:
            if not sampleset in sample_sets_list:
                self.report_warning(spread_sheet_name, None, "The Sample Set ID '"+sampleset+"' (presents in the 'Performance Metrics' spreadsheet) has no linked samples")


    def check_and_remove_whitespaces(self, spread_sheet_name, row_id, label, data):
        """ Check trailing spaces/tabs and remove them """
        if str(data).startswith((' ','\t')) or str(data).endswith((' ','\t')):
            labels = label.split('\n')
            self.report_warning(spread_sheet_name, row_id, f'The column \'{labels[0]}\' (value: \'{data}\') has leading and/or trailing whitespaces.')
            data = data.strip(' \t')
        return data


    def report_error(self, spread_sheet_name, row_id, msg):
        if not spread_sheet_name in self.report['error']:
            self.report['error'][spread_sheet_name] = {}
        # Avoid duplicated message
        if not msg in self.report['error'][spread_sheet_name]:
            self.report['error'][spread_sheet_name][msg] = []
        # Avoid duplicated line reports
        if not row_id in self.report['error'][spread_sheet_name][msg]:
            self.report['error'][spread_sheet_name][msg].append(row_id)

    def report_warning(self, spread_sheet_name, row_id, msg):
        if not spread_sheet_name in self.report['warning']:
            self.report['warning'][spread_sheet_name] = {}
        # Avoid duplicated message
        if not msg in self.report['warning'][spread_sheet_name]:
            self.report['warning'][spread_sheet_name][msg] = []
        # Avoid duplicated line reports
        if not row_id in self.report['warning'][spread_sheet_name][msg]:
            self.report['warning'][spread_sheet_name][msg].append(row_id)

    def add_check_report(self, spread_sheet_name, row_id, check_report_list):
        report_error_list = check_report_list['error']
        if len(report_error_list) > 0:
            for check_report in report_error_list:
                self.report_error(spread_sheet_name,row_id,check_report)
        report_warning_list = check_report_list['warning']
        if len(report_warning_list) > 0:
            for check_report in report_warning_list:
                self.report_warning(spread_sheet_name,row_id,check_report)


    def str2metric(self, field, val, row_id, spread_sheet_name, wb_spreadsheet):
        _, ftype, fname = field.split('_')

        # Find out what type of metric it is
        ftype_choices = {
            'other' : 'Other Metric',
            'beta'  : 'Effect Size',
            'class' : 'Classification Metric'
        }
        current_metric = {'type': ftype_choices[ftype]}

        # Find out if it's a common metric and stucture the information
        fname_common = {
            'OR': ('Odds Ratio', 'OR'),
            'HR': ('Hazard Ratio', 'HR'),
            'AUROC': ('Area Under the Receiver-Operating Characteristic Curve', 'AUROC'),
            'Cindex': ('Concordance Statistic', 'C-index'),
            'R2': ('Proportion of the variance explained', 'R²'),
        }
        if fname in fname_common:
            current_metric['name'] = fname_common[fname][0]
            current_metric['name_short'] = fname_common[fname][1]
        elif (ftype == 'beta') and (fname == 'other'):
            current_metric['name'] = 'Beta'
            current_metric['name_short'] = 'β'
        else:
            fname, val = val.split('=')
            current_metric['name'] = fname.strip()

        # Parse out the confidence interval and estimate
        if type(val) == float:
            current_metric['estimate'] = val
        else:
            matches_square = insquarebrackets.findall(val)
            #Check if an alternative metric has been declared
            if '=' in val:
                mname, val = [x.strip() for x in val.split('=')]
                # Check if it has short + long name
                matches_parentheses = inparentheses.findall(mname)
                if len(matches_parentheses) == 1:
                    current_metric['name'] = mname.split('(')[0]
                    current_metric['name_short'] = matches_parentheses[0]

            #Check if SE is reported
            matches_parentheses = inparentheses.findall(val)
            if len(matches_parentheses) == 1:
                val = val.split('(')[0].strip()
                try:
                    current_metric['estimate'] = float(val)
                except:
                    val, unit = val.split(" ", 1)
                    current_metric['estimate'] = float(val)
                    current_metric['unit'] = unit
                current_metric['se'] = matches_parentheses[0]

            else:
                current_metric['estimate'] = float(val.split('[')[0])
                if len(matches_square) == 1:
                    if re.search(interval_format, matches_square[0]):
                        current_metric['ci'] = matches_square[0]
                        [min_ci,max_ci] = current_metric['ci'].split(' - ')
                        min_ci = float(min_ci)
                        max_ci = float(max_ci)
                        estimate = float(current_metric['estimate'])
                        # Check that the estimate is within the interval
                        if not min_ci <= estimate <= max_ci:
                            self.report_error(spread_sheet_name,row_id,f'The estimate value ({estimate}) is not within its the confidence interval [{min_ci} - {max_ci}]')
                    else:
                        self.report_error(spread_sheet_name,row_id,f'Confidence interval "{val}" is not in the expected format (e.g. "1.00 [0.80 - 1.20]")')

        if not 'name_short' in current_metric:
            current_metric['name_short'] = current_metric['name']

        metric_obj = Metric(
            current_metric['name'],
            current_metric['name_short'],
            current_metric['type'],
            current_metric['estimate']
        )

        metric_obj = complete_object(wb_spreadsheet, metric_obj, current_metric)

        return metric_obj


    def str2demographic(self, val, row_id, spread_sheet_name, wb_spreadsheet):
        current_demographic = {}
        if type(val) == float:
            current_demographic['estimate'] = val
        else:
            #Split by ; in case of multiple sub-fields
            l = val.split(';')
            for x in l:
                name, value = x.split('=')
                name = name.strip()
                value = value.strip()

                # Check if it contains a range item
                matches = insquarebrackets.findall(value)
                if len(matches) == 1:
                    range_match = tuple(map(float, matches[0].split(' - ')))
                    if re.search(interval_format, matches[0]):
                        current_demographic['range'] = matches[0]
                    else:
                        self.report_error(spread_sheet_name,row_id,"Data Range for the value '"+str(value)+"' is not in the expected format (e.g. '1.00 [0.80 - 1.20]')")
                    current_demographic['range_type'] = name.strip()
                else:
                    if name.lower().startswith('m'):
                        current_demographic['estimate_type'] = name.strip()
                        with_units = re.match("([-+]?\d*\.\d+|\d+) ([a-zA-Z]+)", value, re.I)
                        if with_units:
                            items = with_units.groups()
                            current_demographic['estimate'] = items[0]
                            current_demographic['unit'] = items[1]
                        else:
                            current_demographic['estimate'] = value

                    elif name.lower().startswith('s'):
                        current_demographic['variability_type'] = name.strip()
                        with_units = re.match("([-+]?\d*\.\d+|\d+) ([a-zA-Z]+)", value, re.I)
                        if with_units:
                            items = with_units.groups()
                            current_demographic['variability']  = items[0]
                            current_demographic['unit'] = items[1]
                        else:
                            current_demographic['variability'] = value

        demographic = Demographic()
        demographic = complete_object(wb_spreadsheet, demographic, current_demographic)

        return demographic


def get_column_name_index(worksheet, row_index=1):
    col_names = {}
    index = 0
    for row in worksheet.iter_rows(min_row=row_index, max_row=row_index, values_only=True):
        for col in row:
            if col:
                col_names[col] = index
            index += 1
    return col_names


def load_GWAScatalog(outdir):
    ancestry_filename = 'gwas-catalog-ancestry.csv'
    if outdir.endswith('/'):
        loc_local = outdir + ancestry_filename
    else:
        loc_local = '%s/%s' % (outdir, ancestry_filename)

    remap_gwas_model = { 'PUBMEDID' : 'source_PMID',
                         'NUMBER OF INDIVDUALS' : 'sample_number',
                         'BROAD ANCESTRAL CATEGORY' : 'ancestry_broad',
                         'COUNTRY OF ORIGIN' : 'ancestry_free',
                         'COUNTRY OF RECRUITMENT' : 'ancestry_country',
                         'ADDITONAL ANCESTRY DESCRIPTION' : 'ancestry_additional'
                       }
    gwas_data = {}
    with open(loc_local, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            # Skip header
            if line_count == 0:
                continue
            if row["STAGE"] == 'initial':
                gcst_id = row['STUDY ACCESSION']
                if not gcst_id in gwas_data:
                    gwas_data[gcst_id] = []
                study_data = {}
                for column in remap_gwas_model:
                    pgs_model_attr = remap_gwas_model[column]
                    if row[column] != '':
                        study_data[pgs_model_attr] = row[column]
                gwas_data[gcst_id].append(study_data)
    return gwas_data


def complete_object(wb_spreadsheet, object, object_dict):
    object_attrs = object.__dict__.keys()
    for attr in object_attrs:
        if getattr(object, attr) is None:
            if attr in object_dict:
                if object_dict[attr] is not None:
                    value = object_dict[attr]
                    if re.search('^\=',str(object_dict[attr])):
                        value = calculate_formula(wb_spreadsheet,value)
                    setattr(object, attr, value)
    return object


def calculate_formula(spreadsheet,data):
    """ Parse basic formulas and calculate them """
    calculated_value = data
    # Formulas like: =B1+C1, =B1-C1
    m = re.match('^\=(?P<first_cell>\w\d+)(?P<operator>\-|\+)(?P<second_cell>\w\d+)$', data)
    if m:
        first_cell  = get_cell_value(spreadsheet, m.group('first_cell'))
        second_cell = get_cell_value(spreadsheet, m.group('second_cell'))
        operator = m.group('operator')
        if operator == '-':
            calculated_value = int(first_cell) - int(second_cell)
        elif operator == '+':
            calculated_value = int(first_cell) + int(second_cell)
    else:
        # Formulas like: =SUM(B1:C1), =SUM(B1:C2)
        m = re.match('^\=SUM\((?P<first_col>\w)(?P<first_row>\d+)\:(?P<last_col>\w)(?P<last_row>\d+)\)$', data)
        if m:
            alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            first_index = alpha.index(m.group('first_col'))
            last_index = alpha.index(m.group('last_col'))
            first_row = int(m.group('first_row'))
            last_row = int(m.group('last_row'))
            current_col = alpha[first_index]
            current_index = first_index
            #current_row = first_row
            tmp_calculated_value = 0
            while current_index <= last_index:
                current_row = first_row
                while current_row <= last_row:
                    tmp_calculated_value += get_cell_value(spreadsheet, current_col+str(current_row))
                    current_row += 1
                current_index = alpha.index(current_col)+1
                if current_index <= last_index:
                    current_col = alpha[current_index]
            calculated_value = tmp_calculated_value

    return calculated_value


def get_cell_value(spreadsheet,cell_id):
    """ Extract the cell value, using a workbook spreadsheet and a cell ID (e.g. B2)."""
    if re.search('^\w\d+$',cell_id):
        #print("Cell "+str(cell_id)+": "+str(spreadsheet[cell_id].value))
        return spreadsheet[cell_id].value
    else:
        return None
