import re
import openpyxl


class Formula():
    """ Class parsing and calculating simple Excel formulas (sum). """

    is_parsed = False
    alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self, spreadsheet, cell_data):
        self.spreadsheet = spreadsheet
        self.cell_data = cell_data
        self.calculated_value = cell_data


    def formula2number(self):
        """ 
        Use different parser to find and calculate the formula
        Return: calculated value (integer)
        """
        self.parse_numeric_formula()
        if not self.is_parsed:
            self.parse_simple_formula()
        if not self.is_parsed:
            self.parse_sum_formula()

        return self.calculated_value


    def parse_numeric_formula(self):
        """ Parse the formulas of the type: =251+42, =251-42, =251+42-25 """
        cells = re.split('\+|\-', self.cell_data)
        regex_base = '^\=(?P<first_cell>\d+)(?P<operator>\-|\+)(?P<second_cell>\d+)'
        m = None
        # e.g. =251+42
        if len(cells) == 2:
            m = re.match(regex_base+'$', self.cell_data)
        # e.g. =251+42-25
        elif len(cells) == 3:
            m = re.match(regex_base+'(?P<operator2>\-|\+)(?P<third_cell>\d+)$', self.cell_data)

        if m:
            first_cell  = m.group('first_cell')
            second_cell = m.group('second_cell')
            operator = m.group('operator')
            if operator == '-':
                self.calculated_value = int(first_cell) - int(second_cell)
            elif operator == '+':
                self.calculated_value = int(first_cell) + int(second_cell)
            # e.g. =251+42-25
            if len(cells) == 3:
                third_cell = m.group('third_cell')
                operator2 = m.group('operator2')
                if operator2 == '-':
                    self.calculated_value = self.calculated_value - int(third_cell)
                else:
                    self.calculated_value = self.calculated_value + int(third_cell)
            self.is_parsed = True


    def parse_simple_formula(self):
        """ Parse the formulas of the type: =B1+C1, =B1-C1, =B1+C1+D1 """
        cells = re.split('\+|\-', self.cell_data)
        regex_base = '^\=(?P<first_cell>\w\d+)(?P<operator>\-|\+)(?P<second_cell>\w\d+)'
        m = None
        # e.g. =B1+C1
        if len(cells) == 2:
            m = re.match(regex_base+'$', self.cell_data)
        # e.g. =B1+C1+D1
        elif len(cells) == 3:
            m = re.match(regex_base+'(?P<operator2>\-|\+)(?P<third_cell>\w\d+)$', self.cell_data)

        if m:
            first_cell  = self.get_cell_value(m.group('first_cell'))
            second_cell = self.get_cell_value(m.group('second_cell'))
            operator = m.group('operator')
            if operator == '-':
                self.calculated_value = int(first_cell) - int(second_cell)
            elif operator == '+':
                self.calculated_value = int(first_cell) + int(second_cell)
            # e.g. =B1+C1+D1
            if len(cells) == 3:
                third_cell = self.get_cell_value(m.group('third_cell'))
                operator2 = m.group('operator2')
                if operator2 == '-':
                    self.calculated_value = self.calculated_value - int(third_cell)
                else:
                    self.calculated_value = self.calculated_value + int(third_cell)
            self.is_parsed = True


    def parse_sum_formula(self):
        """ Parse the formulas of the type: =SUM(B1:C1), =SUM(B1:C2), =SUM(B1-C2), =SUM(B1+C2) """
        m = re.match('^\=SUM\((?P<first_col>\w)(?P<first_row>\d+)(?P<operator>\-|\+|\:)(?P<last_col>\w)(?P<last_row>\d+)\)$', self.cell_data)
        if m:
            first_col = m.group('first_col')
            last_col = m.group('last_col')
            first_index = self.alpha.index(first_col)
            last_index = self.alpha.index(last_col)
            first_row = int(m.group('first_row'))
            last_row = int(m.group('last_row'))
            operator = m.group('operator')
            # Range of cells
            if operator == ':':
                current_col = self.alpha[first_index]
                current_index = first_index
                tmp_calculated_value = 0
                while current_index <= last_index:
                    current_row = first_row
                    while current_row <= last_row:
                        cell_val = self.get_cell_value(current_col+str(current_row))
                        if cell_val:
                            tmp_calculated_value += cell_val
                        current_row += 1
                    current_index = self.alpha.index(current_col)+1
                    if current_index <= last_index:
                        current_col = self.alpha[current_index]
                self.calculated_value = tmp_calculated_value
            # Operation between 2 cells (addition of substraction)
            else:
                first_cell  = self.get_cell_value(f'{first_col}{first_row}')
                second_cell = self.get_cell_value(f'{last_col}{last_row}')
                if operator == '-':
                    self.calculated_value = int(first_cell) - int(second_cell)
                elif operator == '+':
                    self.calculated_value = int(first_cell) + int(second_cell)
            self.is_parsed = True


    def get_cell_value(self,cell_id):
        """
        Extract the cell value, using a workbook spreadsheet and a cell ID (e.g. B2).
        Make recursive calls to 'formula2number()' if the cell's value is a formula itself.
        """
        if re.search('^\w\d+$',cell_id):
            cell_value = self.spreadsheet[cell_id].value
            # Check if the cell value is also a formula. If so, we calculate the value.
            if re.search('^\=',str(cell_value)):
                cell_subformula = Formula(self.spreadsheet, cell_value)
                cell_value = cell_subformula.formula2number()
            return cell_value
        else:
            return None