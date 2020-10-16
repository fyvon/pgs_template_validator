import re
import pandas as pd

from validator.demographic import Demographic
from validator.efotrait import EFOTrait
from validator.metric import Metric
from validator.performance import PerformanceMetric
from validator.publication import Publication
from validator.sample import Sample
from validator.score import Score

# Needed for parsing confidence intervals
insquarebrackets = re.compile('\\[([^)]+)\\]')
ci_interval_format = '^\d+.?\d*\s\-\s\d+.?\d*$'
inparentheses = re.compile('\((.*)\)')

class PGSMetadataValidator():

    def __init__(self, filepath):
        self.filepath = filepath
        self.parsed_publication = None
        self.parsed_scores = {}
        self.parsed_efotraits = {}
        self.parsed_samples_scores = []
        self.parsed_samples_testing = []
        self.parsed_performances = {}
        self.parsed_samplesets = []
        self.table_mapschema = pd.read_excel('./templates/TemplateColumns2Models_v5.xlsx', index_col = 0)
        self.loc_localGWAS = './local_GWASCatalog/'
        self.report = { 'error': {}, 'warning': {} }



    def parse_spreadsheets(self):
        '''ReadCuration takes as input the location of a study metadata file'''
        loc_excel = self.filepath
        if loc_excel != None:
            self.table_publication = pd.read_excel(loc_excel, sheet_name='Publication Information', header=0, index_col=0)

            self.table_scores = pd.read_excel(loc_excel, sheet_name='Score(s)', header=[0, 1], index_col=0)

            self.table_samples = pd.read_excel(loc_excel, sheet_name='Sample Descriptions', header=0)

            # Parse to separate tables
            self.table_samples_scores = self.table_samples[self.table_samples.iloc[:,1] != 'Testing ']
            self.table_samples_scores.set_index(list(self.table_samples_scores.columns[[0, 1]]), inplace = True)
            self.table_samples_testing = self.table_samples[self.table_samples.iloc[:, 1] == 'Testing ']
            self.table_samples_testing.set_index(list(self.table_samples_testing.columns[[2]]), inplace=True)

            self.table_performances = pd.read_excel(loc_excel, sheet_name='Performance Metrics', header=[0,1], index_col=[0, 1])
            self.table_cohorts = pd.read_excel(loc_excel, sheet_name='Cohort Refr.', header=0, index_col=0)


    def parse_publication(self):
        '''parse_pub takes a curation dictionary as input and extracts the relevant info from the sheet and EuropePMC'''
        #current_schema = self.table_mapschema.loc['Publication Information'].set_index('Column')
        spread_sheet_name = 'Publication'
        pinfo = self.table_publication.loc[spread_sheet_name]

        # DOI
        c_doi = pinfo['doi']

        # PubMed ID
        c_PMID = pinfo[0]
        if c_PMID != '':
            c_PMID = str(c_PMID)
            if not re.search('^\d+$',c_PMID):
                self.report_error(spread_sheet_name,"PubMed ID format should be ony numeric (found: "+c_PMID+")")

        publication = Publication(c_doi, c_PMID)
        publication.populate_from_eupmc()
        publication_check_report = publication.check_data()
        self.add_check_report_error(spread_sheet_name,publication_check_report)

        self.parsed_publication = publication


    def parse_scores(self):
        spread_sheet_name = 'Score(s)'
        current_schema = self.table_mapschema.loc[spread_sheet_name].set_index('Column')
        for score_name, score_info in self.table_scores.iterrows():
            parsed_score = {'name' : score_name }
            for col, val in score_info.iteritems():
                if (col[1] in current_schema.index) and (pd.isnull(val) == False):
                    m, f, _ = current_schema.loc[col[1]]
                    if m == 'Score':
                        if f == 'trait_efo':
                            efo_list = val.split(',')
                            parsed_score[f] = efo_list
                        else:
                            parsed_score[f] = val

            for trait_efo_id in parsed_score['trait_efo']:
                if not trait_efo_id in self.parsed_efotraits:
                    efo_trait = EFOTrait(trait_efo_id)
                    efo_trait.populate_from_efo()
                    if efo_trait.label:
                        self.parsed_efotraits[trait_efo_id] = efo_trait
                    else:
                        self.report_error(spread_sheet_name,"Can't find a corresponding entry in EFO for '"+trait_efo_id+"'")

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
            self.add_check_report_error(spread_sheet_name,score_check_report)

            self.parsed_scores[score_name] = score


    def cohort_to_tuples(self, cstring):
        cohort_df = self.table_cohorts
        clist = []
        for cname in cstring.split(','):
            cname = cname.strip()
            if cname in cohort_df.index:
                clist.append((cname, cohort_df.loc[cname][0]))
            else:
                clist.append((cname, 'UNKNOWN'))
        return clist


    def parse_performances(self):
        spread_sheet_name = 'Performance Metrics'
        current_schema = self.table_mapschema.loc[spread_sheet_name].set_index('Column')

        score_names_list = self.parsed_scores.keys()

        for p_key, performance_info in self.table_performances.iterrows():
            parsed_performance = {
                'score_name': p_key[0],
                'sampleset': p_key[1],
                'metrics': []
            }

            if not parsed_performance['sampleset'] in self.parsed_samplesets:
                self.parsed_samplesets.append(parsed_performance['sampleset'])

            if not parsed_performance['score_name'] in score_names_list:
                self.report_error(spread_sheet_name,"Score name '"+parsed_performance['score_name']+"' from the Performance Metrics spreadsheet can't be found in the Score(s) spreadsheet!")

            for col, val in performance_info.iteritems():
                if pd.isnull(val) == False:
                    l = col[0]
                    if col[1] in current_schema.index:
                        l = col[1]
                    m, f, _ = current_schema.loc[l]
                    if f.startswith('metric'):
                        try:
                            parsed_performance['metrics'].append(str2metric(f, val))
                        except:
                            if ';' in val:
                                for x in val.split(';'):
                                    parsed_performance['metrics'].append(str2metric(f, x))
                            else:
                                print('Error parsing:', f, val)
                    else:
                        parsed_performance[f] = val


            #for pp in parsed_performance:
            #    print(">> "+pp+": "+str(parsed_performance[pp]))
            #score = Score(
            #    parsed_score['name'],#
            #)
            #score.check_data()
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
                self.add_check_report_error(spread_sheet_name,performance_check_report)

                #self.parsed_scores[score_name] = score
                performance_id = parsed_performance['score_name']+'__'+parsed_performance['sampleset']
                self.parsed_performances[performance_id] = performance


    def parse_samples(self):
        spread_sheet_name = 'Sample Descriptions'
        current_schema = self.table_mapschema.loc[spread_sheet_name].set_index('Column')

        # Download and load GWAS data
        #gwas_studies, gwas_samples = load_GWAScatalog(loc_localGWAS, update = True)
        gwas_studies, gwas_samples = load_GWAScatalog(self.loc_localGWAS, update = False)
        gwas_studies.set_index('STUDY ACCESSION', inplace = True)
        gwas_samples.set_index('STUDY ACCESSION', inplace = True)
        gwas_samples = gwas_samples[gwas_samples['STAGE'] == 'initial'] # Get rid of replication studies

        remap_gwas_model = { 'PUBMEDID' : 'source_PMID',
                             'NUMBER OF INDIVDUALS' : 'sample_number',
                             'BROAD ANCESTRAL CATEGORY' : 'ancestry_broad',
                             'COUNTRY OF ORIGIN' : 'ancestry_free',
                             'COUNTRY OF RECRUITMENT' : 'ancestry_country',
                             'ADDITONAL ANCESTRY DESCRIPTION' : 'ancestry_additional'
                           }

        # Extract data for training (GWAS + Score Development) sample
        for sample_ids, sample_info in self.table_samples_scores.iterrows():
            samples = []
            sample_remapped = {}
            for c, val in sample_info.to_dict().items():
                if c in current_schema.index:
                    if pd.isnull(val) == False:
                        f = current_schema.loc[c, 'Field']
                        if f == 'cohorts':
                            val = self.cohort_to_tuples(val)
                        elif f in ['sample_age', 'followup_time']:
                            val = str2demographic(val)
                        sample_remapped[f] = val
            # Parse from GWAS Catalog
            if ('sample_number' not in sample_remapped.keys()):
                if ('source_GWAS_catalog' in sample_remapped) and (sample_remapped['source_GWAS_catalog'] in gwas_samples.index):
                    gwas_results = []
                    gwas_ss = gwas_samples[gwas_samples.index == sample_remapped['source_GWAS_catalog']]
                    for sid, ss in gwas_ss.iterrows():
                        c_sample = sample_remapped.copy()
                        for c, f in remap_gwas_model.items():
                            val = ss[c]
                            if pd.isnull(val) == False:
                                c_sample[f] = val
                        samples.append(c_sample)
            else:
                samples.append(sample_remapped)

            for sample in samples:
                sample_object = Sample(
                    int(sample['sample_number']),
                    sample['ancestry_broad']
                )
                sample_object = complete_object(sample_object,sample)
                sample_check_report = sample_object.check_data()
                self.add_check_report_error(spread_sheet_name,sample_check_report)

                self.parsed_samples_scores.append(sample_object)

        # Extract data Testing samples
        sample_sets_list = []
        for testset_name, testsets in self.table_samples_testing.groupby(level=0):

            if not testset_name in self.parsed_samplesets:
                self.report_warning(spread_sheet_name, "The Sample Set ID '"+testset_name+"' is not present in the Performance Metrics spreadsheet")
            if not testset_name in sample_sets_list:
                sample_sets_list.append(testset_name)

            results = []
            for sample_ids, sample_info in testsets.iterrows():
                sample_remapped = {}
                for c, val in sample_info.to_dict().items():
                    if c in current_schema.index:
                        if pd.isnull(val) == False:
                            f = current_schema.loc[c, 'Field']
                            if pd.isnull(f) == False:
                                if f == 'cohorts':
                                    val = self.cohort_to_tuples(val)
                                elif f in ['sample_age', 'followup_time']:
                                    val = str2demographic(val)

                                sample_remapped[f] = val
                results.append(sample_remapped)

                for sample in results:
                    sample_object = Sample(
                        int(sample['sample_number']),
                        sample['ancestry_broad']
                    )
                    sample_object = complete_object(sample_object,sample)
                    sample_check_report = sample_object.check_data()
                    self.add_check_report_error(spread_sheet_name,sample_check_report)

                    self.parsed_samples_testing.append(sample_object)

        # Check if all the Sample Sets in the Performance Metrics spreadsheet have associated Samples
        for sampleset in self.parsed_samplesets:
            if not sampleset in sample_sets_list:
                self.report_warning(spread_sheet_name, "The Sample Set ID '"+sampleset+"' (presents in the 'Performance Metrics' spreadsheet) has no linked samples")


    def report_error(self,spread_sheet_name,msg):
        if not spread_sheet_name in self.report['error']:
            self.report['error'][spread_sheet_name] = []
        self.report['error'][spread_sheet_name].append(msg)

    def report_warning(self,spread_sheet_name,msg):
        if not spread_sheet_name in self.report['warning']:
            self.report['warning'][spread_sheet_name] = []
        self.report['warning'][spread_sheet_name].append(msg)


    def add_check_report_error(self,spread_sheet_name,check_report_list):
        if len(check_report_list) > 0:
            for check_report in check_report_list:
                self.report_error(spread_sheet_name,check_report)




def load_GWAScatalog(outdir, update = False):
    dl_files = ['studies_ontology-annotated', 'ancestry']
    o = []
    for fn in dl_files:
        loc_local = '%s/gwas-catalog-%s.csv' % (outdir, fn)
        if outdir.endswith('/'):
            loc_local = outdir + 'gwas-catalog-%s.csv' %fn
        if update:
            print('Downloading: %s'%fn)
            df = pd.read_table('ftp://ftp.ebi.ac.uk/pub/databases/gwas/releases/latest/gwas-catalog-%s.tsv'%fn, index_col= False, sep = '\t')
            df.to_csv(loc_local, index = False)
        else:
            df = pd.read_csv(loc_local, index_col=False)
        o.append(df)
    return o


def complete_object(object, object_dict):
    object_attrs = object.__dict__.keys()
    for attr in object_attrs:
        if getattr(object, attr) is None:
            if attr in object_dict:
                if object_dict[attr] is not None:
                    setattr(object, attr, object_dict[attr])
    return object


def str2metric(field, val):
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
                if re.search(ci_interval_format, matches_square[0]):
                    current_metric['ci'] = matches_square[0]
                else:
                    self.report_error("Performance Metrics","Confidence interval '["+matches_square[0]+"]' is not in the right format (e.g. '1.00 [0.80 - 1.20]')")

    metric_obj = Metric(
        current_metric['name'],
        current_metric['name_short'],
        current_metric['type'],
        current_metric['estimate']
    )
    metric_obj = complete_object(metric_obj, current_metric)
    #if 'unit' in current_metric:
    #    metric_obj.unit = current_metric['unit']
    #if 'se' in current_metric:
    #    print('se: '+str(current_metric['se']))
    #    metric_obj.se = current_metric['se']
    #if 'ci' in current_metric:
    #    metric_obj.ci = current_metric['ci']

    return metric_obj


def str2demographic(val):
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
                current_demographic['range'] = NumericRange(lower=range_match[0], upper=range_match[1], bounds='[]')
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
    demographic = complete_object(demographic, current_demographic)

    #print(val, current_demographic)
    return demographic
