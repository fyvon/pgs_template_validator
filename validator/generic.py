import re


class GenericValidator():

    column_types = {
        'string' : 'string',
        'integer': 'number (no decimal)',
        'float': 'number (with decimal)',
        '^\-?\d+(e-|\.)?\d*\s\-\s\-?\d+(e-|\.)?\d*$': 'interval (e.g. 1.00 [0.80 - 1.20] or 0.0231 [-5e-04 - 0.0345])',  # FIXME: invalid escape sequence
        '^EFO\.\d{7}$': 'EFO ID, e.g. EFO_0001645'  # FIXME: invalid escape sequence
    }

    error_value_max_length = 25

    def __init__(self, object, fields_infos, mandatory_fields, type):
        self.object = object
        self.type = type
        self.fields_infos = fields_infos
        self.mandatory_fields = mandatory_fields
        self.report = {'error': [], 'warning': []}


    def add_error_report(self, msg):
        self.report['error'].append(msg)

    def add_warning_report(self, msg):
        self.report['warning'].append(msg)

    def check_not_null(self):
        object_attrs = self.object.__dict__.keys()
        for field in self.mandatory_fields:
            if field.startswith('__'):
                continue
            column_label = self.fields_infos[field]['label']
            if not field in object_attrs:
                self.add_error_report('Mandatory data from '+self.type+" column '"+column_label+"' is missing")
            else:
                column_data = str(getattr(self.object, field))
                if column_data is None or column_data == 'None':
                    self.add_error_report(self.type+" column '"+column_label+"' can't be null in the "+self.type+" object")


    def check_format(self):
        object_attrs = self.object.__dict__.keys()
        for field in self.fields_infos.keys():
            column_label = self.fields_infos[field]['label']
            if field in object_attrs:
                column_data = str(getattr(self.object, field))
                #print("COLUMN "+column+": "+str(column_data)+" | TYPE: "+str(type(column_data)))
                # Skip empty columns
                if column_data is not None and column_data != 'None':
                    field_type = self.fields_infos[field]['type']
                    is_correct_format = 0

                    # Check trailing spaces
                    column_data = self.check_whitespaces(field,column_data)

                    if field_type in self.column_types:
                        column_type_label = self.column_types[field_type]
                    else:
                        column_type_label = field_type

                    if field_type == 'integer':
                        # Also allow float finishing by .0 and .00
                        if re.search('^-?\d+(?:\.0+)?$', column_data):  # FIXME: invalid escape sequence
                            is_correct_format = 1
                    elif field_type == 'float':
                        try:
                            column_data = float(column_data)
                            is_correct_format = 1
                        except ValueError:
                            is_correct_format = 0
                    elif field_type == 'string':
                        is_correct_format = 1
                    else:
                        if re.search(field_type, column_data):
                            is_correct_format = 1

                    if is_correct_format == 0:
                        error_value = str(column_data)
                        if len(error_value) > self.error_value_max_length:
                            error_value = error_value[0:self.error_value_max_length]+'...'
                        self.add_error_report(f'The content of the {self.type} column \'{column_label}\' (i.e.: "{error_value}") is not in the required format/type ({column_type_label}) or has unexpected special character(s).')


    def check_value(self, field:str, allowed_values:list):
        """ Check that the value is found in the list of allowed values. """
        object_attrs = self.object.__dict__.keys()
        if field in self.fields_infos.keys() and field in object_attrs:
           column_label = self.fields_infos[field]['label']
           value = str(getattr(self.object, field))
           if not value in allowed_values:
               self.add_error_report(f'The value \'{value}\' of the column \'{column_label}\' is not in the list of allowed values: [{", ".join(allowed_values)}].')


    def check_whitespaces(self, label, c_data):
        """ Check trailing spaces/tabs and remove them """
        if str(c_data).startswith((' ','\t')) or str(c_data).endswith((' ','\t')):
            self.add_warning_report(f'The content of the {self.type} column \'{label}\' (i.e.: "{c_data}") has leading and/or trailing whitespaces.')
            c_data.strip(' \t')
        return c_data
