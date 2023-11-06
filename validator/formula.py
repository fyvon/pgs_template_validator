import re


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
        try:
            cells = re.split('\+|\-', self.cell_data)
            regex_base = '^\=(?P<cell_1>\d+)'
            regex_formula = regex_base
            if len(cells) > 1:
                regex_formula = regex_formula+'(?P<operator_1>\-|\+)(?P<cell_2>\d+)'
                # e.g. =251+42-25
                if len(cells) > 2:
                    for idx in range(2,len(cells)):
                        next_idx = idx + 1
                        regex_formula =  regex_formula+f'(?P<operator_{idx}>\-|\+)(?P<cell_{next_idx}>\d+)'
            regex_formula = regex_formula+'$'
            m = re.match(regex_formula, self.cell_data)

            if m:
                val_a = 0
                if len(cells) == 1:
                    val_a = int(m.group(f'cell_1'))
                else:
                    last_idx = None
                    for idx in range(1,len(cells)):
                        next_cell = idx+1
                        operator = m.group(f'operator_{idx}')
                        if last_idx != idx:
                            val_a = m.group(f'cell_{idx}')
                        val_b = m.group(f'cell_{next_cell}')
                        last_idx = next_cell
                        if operator == '-':
                            val_a = int(val_a) - int(val_b)
                        elif operator == '+':
                            val_a = int(val_a) + int(val_b)
                self.calculated_value = val_a
                if isinstance(self.calculated_value, int):
                    self.is_parsed = True
        except Exception as e:
            print(f"###### Cell value '{self.cell_data}' is not numeric: {e}")



    def parse_simple_formula(self):
        """ Parse the formulas of the type: =B1+C1, =B1-C1, =B1+C1+D1 """
        print(f"!!!! {self.cell_data} -> parse_simple_formula")
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
            if isinstance(self.calculated_value, int):
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
            if isinstance(self.calculated_value, int):
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