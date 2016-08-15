from IPython.core.magic import (register_line_magic, register_cell_magic,
                                register_line_cell_magic)
import IPython
js = "IPython.CodeCell.config_defaults.highlight_modes['magic_sql'] = {'reg':[/^%%sql/]};"
IPython.core.display.display_javascript(js, raw=True)

class HTMLTable(list):
    """
    Creates an HTML table if pandas isn't installed.
    The .empty attribute takes the place of df.empty,
    and to_csv takes the place of df.to_csv.
    """
    
    empty = []
    
    def _repr_html_(self):
        table = '<table width=100%>'
        thead = '<thead><tr>'
        tbody = '<tbody><tr>'
        for n,row in enumerate(self):
            if n == 0:
                thead += ''.join([('<th>' + str(r) + '</th>') for r in row])
            else:
                tbody += '<tr>' + ''.join([('<td>' + str(r) + '</td>') for r in row]) + '</tr>'
        thead += '</tr></thead>'
        tbody += '</tbody>'
        table += thead + tbody
        return table

    def to_csv(self, path):
        import csv
        with open(path, 'w') as fp:
            a = csv.writer(fp, delimiter=',')
            a.writerows(self)
    
try:
    import pandas as pd
    pd.options.display.max_columns = None
    to_table = pd.DataFrame
except ImportError as e:
    to_table = HTMLTable
    
# default connection string info here
driver = 'postgresql'
username = 'username'
password = 'password'
host = 'host'
port = '5432'

@register_line_cell_magic
def sql(path, cell=None):
    """
    Create magic cell function to treat cell text as SQL
    to remove the need of third party SQL interfaces. The 
    args are split on spaces so don't use spaces except to 
    input a new argument.
    Args:
        PATH (str): path to write dataframe to in csv.
        PARAMS (dict): allows SQLAlchemy named parameters.
        MAKE_GLOBAL: make dataframe available globally.
        DB: name of database to connect to.
    Returns:
        DataFrame:
    """
    args = path.split(' ')
    for i in args:
        if i.startswith('MAKE_GLOBAL'):
            glovar = i.split('=')
            exec(glovar[0]+'='+glovar[1]+'=None')
        elif i.startswith('DB'):
            from sqlalchemy import create_engine
            db = i.replace('DB=', '')
            exec("global engine\nengine=create_engine('"+driver+"://"+username+":"+password+"@"+host+":"+port+"/"+db+"')")
            exec('global DB\nDB=db')
        else:
            exec(i)
            
    if 'PARAMS' in locals():
        for i in PARAMS.keys():
            ref = '%('+i+')s'
            if ref in cell:
                cell = cell.replace(ref, ("'"+(str(eval(i)))+"'" if eval(i) != 'null' else 'null'))

    data = engine.execute(cell)
    columns = data.keys()
    table_data = [i for i in data] if 'pd' in globals() else [columns] + [i for i in data]
    df = to_table(table_data)
    
    if df.empty:
        return 'No data available'
    
    df.columns = columns

    if 'PATH' in locals():
        df.to_csv(PATH)

    if 'MAKE_GLOBAL' in locals():
        exec('global ' + glovar[1] + '\n' + glovar[1] + '=df')
        
    return df