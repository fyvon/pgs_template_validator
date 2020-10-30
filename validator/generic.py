import re


class GenericValidator():

    column_labels = {
        'string' : 'string',
        'integer': 'number (no decimal)',
        'float': 'number (with decimal)',
        '^\d+\.?\d*\s\-\s\d+\.?\d*$': 'interval (e.g. [1.00 [0.80 - 1.20])',
        '^EFO\.\d{7}$': 'EFO ID, e.g. EFO_0001645'
    }

    error_value_max_length = 25

    def __init__(self, object, type):
        self.object = object
        self.type = type
        self.report = {'error': [], 'warning': []}


    def add_error_report(self, msg):
        self.report['error'].append(msg)

    def add_warning_report(self, msg):
        self.report['warning'].append(msg)

    def check_not_null(self):
        object_attrs = self.object.__dict__.keys()
        for column in self.object.not_null_columns:
            if not column in object_attrs:
                self.add_error_report(self.type+" column '"+column+"' is not in the "+self.type+" object")
            else:
                column_data = str(getattr(self.object, column))
                if column_data is None or column_data == 'None':
                    self.add_error_report(self.type+" column '"+column+"' can't be null in the "+self.type+" object")


    def check_format(self):
        object_attrs = self.object.__dict__.keys()
        for column in self.object.column_format.keys():

            if not column in object_attrs:
                self.add_error_report(self.type+" column '"+column+"' is not in the "+type+" object")
            else:
                column_data = str(getattr(self.object, column))
                #print("COLUMN "+column+": "+str(column_data)+" | TYPE: "+str(type(column_data)))
                # Skip empty columns
                if column_data is not None and column_data != 'None':
                    column_format = self.object.column_format[column]
                    column_label = column_format
                    is_correct_format = 0

                    if column_format in self.column_labels:
                        column_label = self.column_labels[column_format]
                    if column_format == 'integer':
                        if re.search('^-?\d+$', column_data):
                            is_correct_format = 1
                    elif column_format == 'float':
                        #print("FLOAT: "+column+" | TYPE: "+str(type(column_data)))
                        #if re.search('\d+e-?\d+$',column_data, re.IGNORECASE):
                        #    column_data = float(column_data)
                        #    print("AFTER: "+str(column_data))
                        #if re.search('^-?\d+\.\d+$', column_data) or re.search('^-?\d+$', column_data):
                        #    is_correct_format =
                        try:
                            column_data = float(column_data)
                            is_correct_format = 1
                        except ValueError:
                            is_correct_format = 0
                    elif column_format == 'string':
                        if re.search('^.+$', column_data):
                            is_correct_format = 1
                    else:
                        if re.search(column_format, column_data):
                            is_correct_format = 1

                    if is_correct_format == 0:
                        error_value = str(column_data)
                        if len(error_value) > self.error_value_max_length:
                            error_value = error_value[0:self.error_value_max_length]+'...'
                        self.add_error_report(f'{self.type} column \'{column}\' (value: \'{error_value}\') is not in the required format/type ({column_label}) or has unexpected special character(s).')
