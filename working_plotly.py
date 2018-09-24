import base64
import io
import json
import dash_table_experiments as dt
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
#import numpy as np

# Start the dash app
app = dash.Dash()
# For testing vv
pd.set_option('display.expand_frame_repr', False)
# CSS is taken from this video https://www.youtube.com/watch?v=f2qUWgq7fb8&feature=youtu.be
# and app layout is somewhat similar.
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'})
#app.scripts.config.serve_locally = True

# The layout of the dash app
#   Title                          filSep  Header       Drag and Drop
#                                  |Dropdown| |dropdown|
##################################################################
#   Xlabel      Ylabel      CategoryLabel       TextLabel
#  | Dropdown | | Dropdown |  | Dropdown |   |Dropdown|
###################################################################
#                               GRAPH
#                               GRAPH
#                               GRAPH
#                               GRAPH
#                               GRAPH
#####################################################################
#   Logtransform Label    Search Bar
#   |   Dropdown |       | Seach here               | |Button |
#####################################################################
#                             DATATable
#                             DATATable
#                             DATATable
#                             DATATable
#####################################################################

app.layout = html.Div([
    html.Div(id="hidden_data", style={'display':'none'}),
    html.Div(id="hidden_header", style={'display': 'none'}),
    html.Div([
       html.Div([
           html.H5(
               children='Plot your CSVs\n',

           ),
           html.P(
               children='Select file sep, header row, then upload file. Once uploaded select all corresponding dropdowns '
                        'to render graph.'
           )

       ], className='six columns'),
        html.Div([
            html.Label('File seperator'),
            dcc.Dropdown(
                id='radio_button',
                options=[
                    {'label': 'TSV', 'value': 'tab_sep'},
                    {'label': 'CSV', 'value': 'comma_sep'}
                ]
            )
        ], className='one columns'),
        html.Div([
            html.Label('Header row?'),
            dcc.Dropdown(
                id='header_drop',
                options=[
                    {'label': 'Yes', 'value': 'header_1'},
                    {'label': 'No', 'value': 'header_0'}
                ]
            )
        ], className='one columns'),
        html.Div([
           dcc.Upload(
            id="csv-upload",
            children=html.Div([
                "Drag and drop or", html.A(" Select File")
            ]),
            className='three columns',
            style={
               'height': '100%',
               'width': '25%',
               'float': 'right',
               'position': 'relative',
               'borderWidth': '1px',
               'borderStyle': 'dashed',
               'borderRadius': '5px',
               'textAlign': 'center',
               'margin': '30px',
               'background-color':'#FEFEFE'

            },
           )
        ], id='hidden_upload', style={'visibility': 'hidden'})
     ], style={'background-color': '#E6E6E6', 'border-style': 'solid', 'border-width': '2px'} , className='row'),
    html.Div([
        html.Div([
            html.Label('X-Axis coords'),
            dcc.Dropdown(
                id='xaxis_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Y-Axis coords'),
            dcc.Dropdown(
                id='yaxis_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Category'),
            dcc.Dropdown(
                id='category_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Text column(s)'),
            dcc.Dropdown(
                id='multi_drop',
                multi=True,

            )
        ], className='three columns'),
        html.Div([
            html.Label('Other graph'),
            dcc.Dropdown(
                id='species_drop'
            )
        ], className='one column'),
        html.Div([
            html.Label('Graph options'),
            dcc.Dropdown(
                id='species_graph'
            )
        ], className='one column')
    ], id='main_div', style={'visibility': 'hidden'}, className='row'),
    #
    # Maybe add these back in when datatable functionallity changes
    html.Div([
        html.Div([
            html.Label('Ensemble column'),
            dcc.Dropdown(
                id='ensmbl_drop',
                value="N/A"
            )
        ], id='ensmbl_div', style={'visibility': 'hidden'}, className='three columns'),
        html.Div([
            html.Label('Ncbi column'),
            dcc.Dropdown(
                id='ncbi_drop',
                value="N/A"
            )
        ], id='ncbi_div', style={'visibility': 'hidden'}, className='three columns')
    ], className='row'),
    html.Div([
        html.Div([
            dcc.Graph(
                id="Scatter-Graph",
                #clickData={'points'}
            )
        ], className='twelve columns')
    ], style={'border-style': 'solid', 'border-width': '2px', 'margin-top':'5px'}, className='row'),
    html.Div([
        html.Div([
            html.Label('Log transform axes'),
            dcc.Dropdown(
                id='log_trans'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Sort numerical'),
            dcc.Dropdown(
                id='num_trans'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Search for points in graph. (Searches columns set in the text columns drop down).'),
            dcc.Input(
                id='search_box',
                placeholder='Case sensitive search',
                style={'width': '100%',
                       'height': '100%',
                       'padding-top': '18px',
                       'font-size':'12px'
                }
            )
        ], className='six columns'),
        html.Div([
            html.Button('Search.',
                        id='search_button',
                        style={'margin-top': '23px',
                               'margin-left': '10px',
                               'background-color': '#FEFEFE'})
        ], className='one column')
    ], style={'background-color': '#E6E6E6', 'border-style': 'solid', 'border-width': '2px'}, className='row'),
    html.Div([
       html.Div([
        ], className='twelve columns', id='dtable_div')
    ], className='row')
])



# Function to pull a dataframe from a user uploaded csv
def parse_csv(contents, filename, sep_radio, header):
    # Don't do anything if the variables aren't set
    if contents is None:
        exit(1)
    if sep_radio is None:
        exit(1)

    # If the separator drop drown is CSV / TSV do the corresponding split.
    if sep_radio == "comma_sep":
        content_type, content_string = contents.split(",")
    elif sep_radio == "tab_sep":
        content_type, content_string = contents.split("\t")

    # Decode the file
    decoded = base64.b64decode(content_string)

    # Make a data frame with pandas
    # Check if the user has specified a header or not.
    if header == "header_1":
        df = pd.read_csv(io.StringIO(decoded.decode('utf8')), header=0)
    else:
        df = pd.read_csv(io.StringIO(decoded.decode('utf8')), header=None)

        # If there is no header make a new header like this
        # Column 1 Column 2 etc, etc
        df.columns = ["Column " + str(i) for i in range(1, len(df.columns.values) + 1)]

    return df
########################    Call back to update hidden & show drop downs    ############################

# Can't currently add clickable links to dash datatables see:
# https://github.com/plotly/dash-table-experiments/pull/11

@app.callback(
    Output('ensmbl_drop', 'options'),
    [Input('multi_drop', 'value')]
)
def update_ensemble(drop):
    if drop is None or len(drop) == 0:
        exit(1)
    else:
        print(drop)
        return [{'label': i, 'value': i} for i in drop]


@app.callback(
    Output('ensmbl_div', 'style'),
    [Input('multi_drop', 'value')]
)
def show_ensmble(drop):
    if drop is None or len(drop) == 0:
        exit(1)
    else:
        return {'visiblity': 'show', 'margin-top': '10px'}

#######################################################################

@app.callback(
    Output('ncbi_drop', 'options'),
    [Input('multi_drop', 'value')]
)
def update_ncbi(drop):
    if drop is None or len(drop) == 0:
        exit(1)
    else:
        print(drop)
        return [{'label': i, 'value': i} for i in drop]

@app.callback(
    Output('ncbi_div', 'style'),
    [Input('multi_drop', 'value')]
)
def show_ncbi(drop):
    if drop is None or len(drop) == 0:
        exit(1)
    else:
        return {'visiblity': 'show', 'margin-top': '10px'}


########################    Call back to show upload after values set    ############################
@app.callback(
    Output('hidden_upload', 'style'),
    [Input('radio_button', 'value'),
     Input('header_drop', 'value')]
)
def show_upload(v1, v2):
    if v1 is None or v2 is None:
        return {'visibility': 'hidden'}
    else:
        return {'visibility': 'visible'}
########################    Call back to upload df to hidden div    ############################
@app.callback(
    Output('hidden_data', 'children'),
    [Input("csv-upload", "contents"),
    Input("csv-upload", "filename")],
    [State("radio_button", 'value'),
     State("header_drop", 'value')]
)
def get_file(file_contents, file_name, radio, header):
    df = parse_csv(file_contents, file_name, radio, header)

    # Read the csv and save it in the hidden div as json.
    # Needs to be json.
    return df.to_json(date_format='iso', orient='split')
@app.callback(
    Output('hidden_header', 'children'),
    [Input('hidden_data', 'children')]
)
def store_headers(data):
    if data is None:
        exit(1)
    else:
        df = (pd.read_json(data, orient='split'))
        return json.dumps(list(df.columns.values))
########################    Call back to show div after successful file upload    ############
@app.callback(
    Output('main_div', 'style'),
    [Input('hidden_data', 'children')]
)
def show_main_div(data):
    return {'visibility': 'visible'}
#######################     Callbacks to populate drop downs     #############################
@app.callback(
    Output('multi_drop', 'options'),
    [Input('hidden_header', 'children')]
)
def update_multi(data):
    name = json.loads(data)

    name.append("N/A")
    return [{'label': i, 'value': i} for i in name]
@app.callback(
    Output('xaxis_drop', 'options'),
    [ Input('hidden_header', 'children')]

)
# This call back and all the other dropdown updates follow the same workflow as this.
# Read the comments for this one vvvvvvvv
def update_x_drop(data):
    # Decode the json dataframe which was stored on users browser.
    names = json.loads(data)
    # For each column header make it a drop down option.
    return [{'label': i, 'value': i} for i in names]

@app.callback(
    Output('species_drop','options'),
    [Input('hidden_header', 'children')]
)
def update_spec_drop(data):
    names = json.loads(data)
    return [{'label': i, 'value': i} for i in names]

@app.callback(
    Output('species_graph', 'options'),
    [Input('species_drop', 'value'),
     Input('hidden_data', 'children')]
)
def update_spec_graph(val, data):
    df = pd.read_json(data, orient='split')
    if val is None:
        exit(1)
    return [{'label': i, 'value': i} for i in df[val].unique()]

@app.callback(
    Output('yaxis_drop', 'options'),
    [ Input('hidden_header', 'children')]
)
def update_y_drop(data):
    names = json.loads(data)
    return [{'label': i, 'value': i} for i in names]


@app.callback(
    Output('category_drop', 'options'),
    [ Input('hidden_header', 'children')]
)
def update_cat_drop(data):
    names = json.loads(data)
    names.append("N/A")
    return [{'label': i, 'value': i} for i in names]

@app.callback(
    Output('log_trans', 'options'),
    [Input('xaxis_drop', 'value'),
     Input('yaxis_drop', 'value')]
)
def update_logs(x, y):
    if x is None or y is None:
        exit(1)
    names = []
    names.append(x)
    names.append(y)
    x_y = x + " + " +y
    names.append(x_y)
    names.append("Reset Axes")

    return [{'label': i, 'value': i} for i in names]

@app.callback(
    Output('num_trans', 'options'),
    [Input('xaxis_drop', 'value'),
     Input('yaxis_drop', 'value')]
)
def update_numeric(x, y):
    if x is None or y is None:
        exit(1)
    names = []
    names.append(x)
    names.append(y)
    names.append("Reset Axes")

    return [{'label': i, 'value': i} for i in names]

####################################################################################
###########################     Callback to update graph     #######################
@app.callback(
    Output('Scatter-Graph', 'figure'),
    [Input('xaxis_drop', 'value'),
     Input('yaxis_drop', 'value'),
     Input('category_drop', 'value'),
     Input('hidden_data', 'children'),
     Input('multi_drop', 'value'),
     Input('search_button', 'n_clicks'),
     Input('log_trans', 'value'),
     Input('num_trans', 'value'),
     Input('species_graph', 'value')],
    [State('search_box', 'value'),
     State('species_drop', 'value')]

)
# Gets input values from all of the drop down menus.
# Updates when any of these values are changed.
def update_graph(xaxis, yaxis, category, hidden, mval, search_button, logs, nums, species,search, species_val):

    # If any of the three values are not set don't do anything.
    if xaxis is None or yaxis is None or category is None or mval is None:
        exit(1)
    # Read the json dataframe stored in the users browser.
    df = pd.read_json(hidden, orient='split')
    if species is None:
        df = df
    else:
        df = df[df[species_val] == species]
        #df = df[df[species_val == species]]

    df_list = []
    # For the search functionallity vv
    if search is not None and "N/A" not in mval:
        for i in mval:
            # Treat each column the user has chose in the text dropdown
            # As a column to search string for.
            # Partial string search using Pandas.
            df_list.append(df[df[i].str.contains(search, na=False)])

        # You get separate dataframes for each separate text column so concat them together.
        df = pd.concat(df_list)

    # Functions to deal with log scaling the plots. Both follow the same logic
    # So just read the comments for this one.
    def logs_x(lst, x, y):
        # If the log transform dropdown doesnt exists of the user selects reset axes
        # Don't do anything to the axis other than name it.
        if lst is None or len(lst) == 0 or "Reset Axes" in lst:
            return {'title': str(x)}

        # If theyve selected to log x axis or x and y axis
        # tell go.Layout that you want to log.
        else:
            if x in lst or str(x + " + " + y) in lst:
                return {'type': 'log', 'title': str(x)}
            else:
                return {'title': str(x)}

    def logs_y(lst, x, y):
        if lst is None or len(lst) == 0 or "Reset Axes" in lst:
            return {'title': str(y)}
        else:
            if y in lst or str(x + " + " + y) in lst:
                return {'type': 'log', 'title': str(y)}
            else:
                return {'title': str(y)}

    def nums_df(string, axis, frame):
        if string == axis:
            return frame[axis].sort_values(ascending=False)
        elif string == "Reset Axes" or string is None:
            return frame[axis]
        else:
            data = []
            for en, i in enumerate(frame[axis]):
                data.append(en)
            df = pd.DataFrame(data)
            return df.iloc[:,0]


    # If the user hasn't specified a category colum in the drop down do this
    if category == "N/A":
        traces = []
        # If user has specified text columns do this.
        if not "N/A" in mval:
            traces.append(go.Scatter(
                # X-coords
                y=nums_df(nums, yaxis, df),
                # Y-Coords
                x=nums_df(nums, xaxis, df),
                # Separate df for each text column to values
                text=df[[i for i in mval]].values.tolist(),
                mode="markers",
                opacity=0.5
            ))
        else:
            traces.append(go.Scatter(
                y=nums_df(nums, yaxis, df),
                x=nums_df(nums, xaxis, df),
                text="",
                mode="markers",
                opacity=0.5
            ))
        return {
            'data': traces,
            'layout': go.Layout(
                xaxis=logs_x(logs, xaxis, yaxis),
                yaxis=logs_y(logs, xaxis, yaxis),
                hovermode='closest'
            )
        }
    # y = subset_df[yaxis],
    # x = subset_df[xaxis],
    # If the user has specified some categories do this.
    else:
        traces = []
        # For each unique item in the category column the user has specfied
        # subset the dataframe to rows with this value.
        for i in df[category].unique():
            subset_df = df[df[category] == i]

            # If there's is text specified do the same as we did above.
            if not "N/A" in mval:
                traces.append(
                    go.Scatter(
                        y=nums_df(nums, yaxis, subset_df),
                        x=nums_df(nums, xaxis, subset_df),
                        text=subset_df[[i for i in mval]].values.tolist(),
                        mode='markers',
                        name=str(i),
                        opacity=0.5
                    )
                )

            # If there's no text specified just leave the element blank.
            else:
                traces.append(
                    go.Scatter(
                        y=nums_df(nums, yaxis, subset_df),
                        x=nums_df(nums, xaxis, subset_df),
                        text="",
                        mode='markers',
                        name=str(i),
                        opacity=0.5
                    )
                )
        return {
            'data': traces,
            'layout': go.Layout(
            xaxis=logs_x(logs, xaxis, yaxis),
            yaxis=logs_y(logs, xaxis, yaxis),
            hovermode='closest'
            )
        }


###################################################################################
##########################     Callback to update table     #######################
# @app.callback(
#     Output('dtable', 'columns'),
#     [Input('multi_drop', 'value'),
#      Input('xaxis_drop', 'value'),
#      Input('yaxis_drop', 'value')],
#
# )
# # Callback to update the columns in the data table when a user adds an extra text column.
# # Pretty simple stuff.
# def update_columns(mval, xval, yval):
#     if xval is None or yval is None or mval is None:
#         exit(1)
#     if not "N/A" in mval:
#         to_return = [xval] + [yval] + mval
#     else:
#         to_return = [xval] + [yval]
#     return to_return
#

@app.callback(
    Output('dtable_div', 'children'),
    [Input('Scatter-Graph', 'clickData'),
     Input('Scatter-Graph', 'selectedData')],
    [State('multi_drop', 'value'),
     State('xaxis_drop', 'value'),
     State('yaxis_drop', 'value'),
     State('ensmbl_drop', 'value'),
     State('ncbi_drop', 'value')]


)
# Update the table with data from either / both of a box / lassoo select or a click.
def update_table(clicked, selected,  mval, xval, yval, ensmbl, ncbi):

    # A funciton to populate a table and add hyper links into it.
    def table(frame, eb, nc):
        # Store all the row data as we need to return it
        rows = []

        # For each row in the dataframe
        for i in range(len(frame)):

            # Store each row in memory
            row = []
            for col in frame.columns:
                # For each column make a value as this row/col in the df
                value = df.iloc[i][col]

                # If the column in the df is the one the user stated as the ensmble col
                # make it a hyper link.
                # Same goes for ncbi.
                if col == eb:
                    value = value.replace("'", "")
                    cell = html.Td(
                        html.A(
                            href="https://www.ensembl.org/Multi/Search/Results?q="+value+";site=ensembl_all"
                            , children=value)
                    )
                elif col == nc:
                    cell = html.Td(
                        html.A(
                            href="https://www.ncbi.nlm.nih.gov/nuccore/"+value, target='_blank', children=value
                        )
                    )
                # If its not an ensmle or ncbi column dont add a hyper link.
                else:
                    cell = cell = html.Td(children=value)
                # Append cell values to the row
                row.append(cell)
            # append row values to the row
            rows.append(html.Tr(row))

        # Return the formatted html table.
        return html.Table(
            [html.Tr([html.Th(col) for col in df.columns])] + rows
        )

    if clicked is None and selected is None:
        exit(1)

    # If they;ve used the box tool do this.
    if selected is not None:
        coords = json.dumps(selected, indent=2)
        coords = json.loads(coords)

        # Make a simple data frame of all the x and y coords
        xlist = []
        ylist = []
        for i in coords['points']:
            xlist.append(i['x'])
            ylist.append(i['y'])

        data = {str(xval): xlist, str(yval): ylist}
        df = pd.DataFrame(data=data)

        # If there;s no extra data columns we can return at this point.
        if "N/A" in mval:
            return table(df, ensmbl, ncbi)

        # If there is text. For the json of EACH point look at specific indices for the
        # correct text to print to screen.
        # We know the json will only store what we need, so if we enumerate the cols we know
        # exactly where to look.
        # i.e user specifies cols: 8,10,12
        # we enumerate this to indices 0,1,2
        # So we look in the json for ['points'][0], etc
        # This same procedure is followed for the click data, just a lot simpler.
        val_dict = {}
        for i in coords['points']:
            for en, j in enumerate(mval):
                key = str(j)
                val_dict.setdefault(key, [])
                try:
                    val_dict[key].append(i['text'].split("',")[en].replace("]","").replace("[",""))
                except IndexError:
                    val_dict[key].append(i['text'].split(",")[en].replace("]", "").replace("[", ""))

        for i in val_dict:
            df[str(i)] = val_dict[i]

        return table(df, ensmbl, ncbi)

    else:
        coords = json.dumps(clicked, indent=2)
        coords = coords.replace("[","").replace("]","")
        coords = json.loads(coords)
        xcoord = coords['points']['x']
        ycoord = coords['points']['y']
        data = {str(xval): [xcoord], str(yval): [ycoord]}
        df = pd.DataFrame(data=data)
        if "N/A" in mval:
            return table(df, ensmbl, ncbi)
        for en, i in enumerate(mval):
            try:
                df[str(i)] = coords['points']['text'].split("',")[en]
            except IndexError:
                df[str(i)] = coords['points']['text'].split(",")[en]

        return table(df, ensmbl, ncbi)



#######################     Callbacks to clear table     #############################


if __name__ == '__main__':
    app.run_server(debug=True)