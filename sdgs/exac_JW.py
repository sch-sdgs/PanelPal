import openpyxl


def main():
    wb = openpyxl.load_workbook('NGSresultsJW.xls')
    sheets = wb.get_sheet_names()

    for s in sheets:
        sheet = wb.get_sheet_by_name(s)




main()