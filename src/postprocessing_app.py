import pandas as pd
import numpy as np
import tkinter as tk
import csv
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.widgets as wdg
import matplotlib.style as mplstyle
import ast
from pathlib import Path
import time
import sys
from functools import reduce

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

# V1.4.0

ctk.set_appearance_mode('Dark')
mplstyle.use('fast')

def _quit(app):
    app.destroy()
    time.sleep(.1)
    sys.exit()

class BlittedCursor:
    # A cross-hair cursor using blitting for faster redraw.
    
    def __init__(self, ax):
        self.ax = ax
        self.background = None
        self.horizontal_line = ax.axhline(color='.5', lw=0.8, ls='-')
        self.vertical_line = ax.axvline(color='.5', lw=0.8, ls='-')
        self._creating_background = False
        ax.figure.canvas.mpl_connect('draw_event', self.on_draw)


    def on_draw(self, event):
        self.create_new_background()


    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        return need_redraw


    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False


    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            # update the line positions
            x, y = event.xdata, event.ydata
            self.horizontal_line.set_ydata([y])
            self.vertical_line.set_xdata([x])


            self.ax.figure.canvas.restore_region(self.background)
            self.ax.draw_artist(self.horizontal_line)
            self.ax.draw_artist(self.vertical_line)
            self.ax.figure.canvas.blit(self.ax.bbox)


class APP(ctk.CTk):
    def __init__(self):
        super().__init__()

        # configure application window
        self.title('V1.4.0')
        scrn_w = self.winfo_screenwidth() - 100
        scrn_h = self.winfo_screenheight() - 100
        self.config(background='black')
        self.geometry(f'{scrn_w}x{scrn_h}+50+25')
        

        # Grid layout
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=10)
        self.grid_rowconfigure(3, weight=1)
        

        # Add all Variables to applicaiton
        self.font1 = ctk.CTkFont(family='Arial Baltic', size=20, weight='bold')
        self.font2 = ctk.CTkFont(family='Arial Baltic', size=14, weight='bold')

        self.full_df =  None
        self.filtered_df =  None
        self.df_columns =  []
        self.x_axis =  ctk.StringVar()
        
        self.disabled_button =  None
        self.yeti_selection =  ctk.StringVar()
        self.output_selection =  ctk.StringVar()
        self.cycle_selection =  ctk.StringVar()
        self.yeti_list =  []
        self.output_list =  []
        self.cycle_list =  []
        self.parameter_selections =  {}
        self.crosshair_state = ctk.IntVar(value=0)
        self.normalize_state = ctk.IntVar(value=0)
        self.fridgeplexor_import_state = ctk.IntVar(value=0)
        self.mixed_import_state = ctk.IntVar(value=0)
        self.text_filepath1 =  ctk.StringVar(value='File(s): ')
        self.text_filepath2 =  ctk.StringVar()

        self.protocol("WM_DELETE_WINDOW", lambda:_quit(self))
        self.init_frames()

    def init_frames(self):
        # Initializes window, its a function of the application so on a new import all the frames are reinitialized, updating all values

        # Import Frame
        self.import_frame = ctk.CTkFrame(self, width=250, corner_radius=0, bg_color='black', fg_color='grey18')
        self.import_frame.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky='nsew')
        self.import_frame.columnconfigure(0, weight=1)
        self.import_frame.rowconfigure((0,1,2,3,4,5), weight=1)

        self.file_text1 = ctk.CTkLabel(self.import_frame, corner_radius=5, textvariable=self.text_filepath1, fg_color='black', text_color='grey50', font=self.font2, width=250, anchor='w')
        self.file_text1.grid(row=0, column=0, padx=5, pady=[5,0], sticky='new')
        self.file_text2 = ctk.CTkLabel(self.import_frame, corner_radius=5, textvariable=self.text_filepath2, fg_color='black', text_color='grey50', font=self.font2, width=250, anchor='w')
        self.file_text2.grid(row=1, column=0, padx=5, pady=[0,5], sticky='new')

        self.fridgeplexor_import_checkbox = ctk.CTkCheckBox(self.import_frame, text='Fridgeplexor Import', corner_radius=5, hover_color='yellow2', fg_color='black',bg_color='grey18', border_color='black', font=self.font2, text_color='grey50', command=self.fridgeplexor_import_select, variable=self.fridgeplexor_import_state)
        self.fridgeplexor_import_checkbox.grid(row=2, column=0, padx=5, pady=5, sticky='new')

        self.mixed_import_checkbox = ctk.CTkCheckBox(self.import_frame, text='Mixed script Import', corner_radius=5, hover_color='yellow2', fg_color='black',bg_color='grey18', border_color='black', font=self.font2, text_color='grey50', command=self.mixed_import_select, variable=self.mixed_import_state)
        self.mixed_import_checkbox.grid(row=3, column=0, padx=5, pady=5, sticky='new')

        self.import_button = ctk.CTkButton(self.import_frame, corner_radius=5, text='Import File(s)', fg_color='yellow2', text_color='grey18', font=self.font1, command=self.import_file, hover_color='grey50')
        self.import_button.grid(row=4, column=0, padx=10, pady=10, sticky='nsew')

        self.export_button = ctk.CTkButton(self.import_frame, corner_radius=5, text='Export Data', fg_color='grey50', text_color='grey18', state='disabled', font=self.font1, command=self.export_file, hover_color='grey50')
        self.export_button.grid(row=5, column=0, padx=10, pady=10, sticky='nsew')
        

        # Parameter Frame
        self.parameter_frame = ctk.CTkScrollableFrame(self, corner_radius=0, label_text='PARAMETERS', label_font=self.font1, label_fg_color='yellow2', label_text_color='grey18', bg_color='black', fg_color='grey18')
        self.parameter_frame.grid(row=2, column=0, padx=5, pady=5, sticky='nsew')

        self.parameter_switches = {}
        for i, p in enumerate(self.parameter_selections):
            switch = ctk.CTkSwitch(self.parameter_frame, text=p, variable=self.parameter_selections[p], command=self.update_graph, font=self.font2, progress_color='yellow2', fg_color='black', button_color='grey50', text_color='grey50', switch_width=40)
            switch.grid(row=i, column=0, padx=15, pady=5, sticky='ew')
            self.parameter_switches[p] = switch


        # Options Frame
        self.options_frame = ctk.CTkFrame(self, corner_radius=0, bg_color='black', fg_color='grey18')
        self.options_frame.grid(row=3, column=0, padx=5, pady=5, sticky='nsew')
        self.options_frame.columnconfigure(0, weight=1)

        self.options_header = ctk.CTkLabel(self.options_frame, corner_radius=0, fg_color='yellow2', text_color='grey18', text='OPTIONS', font=self.font1)
        self.options_header.grid(row=0, column=0, padx=0, pady=0, sticky='nsew')

        self.normalize_checkbox = ctk.CTkCheckBox(self.options_frame, text='Normalize', corner_radius=5, hover_color='yellow2', fg_color='black',bg_color='grey18', border_color='black', font=self.font2, text_color='grey50',command=self.normalize_data, variable=self.normalize_state)
        self.normalize_checkbox.grid(row=1, column=0, padx=5, pady=5, sticky='nsew' )


        self.crosshair_checkbox = ctk.CTkCheckBox(self.options_frame, text='Crosshair', corner_radius=5, hover_color='yellow2', fg_color='black',bg_color='grey18', border_color='black', font=self.font2, text_color='grey50', variable=self.crosshair_state)
        self.crosshair_checkbox.grid(row=2, column=0, padx=5, pady=5, sticky='nsew' )


        # Graph Frame
        self.graph_frame = ctk.CTkFrame(self, corner_radius=0, bg_color='black', fg_color='grey18')
        self.graph_frame.grid(row=1, column=1, rowspan=3, padx=0, pady=5, sticky='nsew')
        self.graph_frame.rowconfigure(0, weight=1)
        self.graph_frame.columnconfigure(0, weight=1)

        plt.style.use('dark_background')

        fig1, ax1 = plt.subplots()
        plt.grid(color='.5')
        plt.subplots_adjust(left=.05, right=.95, top=.95, bottom=.05)
        self.fig1 = fig1
        self.ax1 = ax1
        self.ax1.spines[['top', 'bottom', 'left', 'right']].set_color('0.18')
        self.ax1.spines[['top', 'bottom', 'left', 'right']].set_linewidth(4)
        self.ax1.xaxis.label.set_color('.5')
        self.ax1.yaxis.label.set_color('.5')

        self.ax1.tick_params(axis='both', width=3, colors='.5', which='both', size=10)

        self.canvas1 = FigureCanvasTkAgg(self.fig1, self.graph_frame)
        self.canvas1.get_tk_widget().grid(row=0, column=0, padx=0, pady=0, sticky='nsew')
        self.canvas1.draw()

        plt.connect('motion_notify_event', lambda event: self.on_move(event, b_c=self.blitted_cursor1))
        plt.connect('key_press_event', self.key_event)
        plt.connect('button_press_event', self.mouse_event)

        self.toolbar = NavigationToolbar2Tk(self.canvas1, self.graph_frame, pack_toolbar=False)
        self.toolbar.grid(row=1, column=0, padx=0, pady=0, sticky='nsew')
        self.toolbar.config(background='grey18', )
        self.toolbar_children = self.toolbar.winfo_children()
        for child in self.toolbar_children:
            child.config(background='grey18')

        self.blitted_cursor1 = BlittedCursor(self.ax1)
 

        # Filter Frame
        self.filter_frame = ctk.CTkFrame(self, height=50, corner_radius=0, bg_color='black', fg_color='grey18')
        self.filter_frame.grid(row=0, column=1, padx=0, pady=5, sticky='nsew')
        self.filter_frame.rowconfigure((0,1), weight=1)
        self.filter_frame.columnconfigure((0,1,2,3,4,5), weight=1)

        self.xaxis_text = ctk.CTkLabel(self.filter_frame, text='X_Axis', font=self.font2, text_color='grey50', bg_color='grey18')
        self.xaxis_text.grid(row=0, column=0, padx=20, pady=1, sticky='nsew')
        self.xaxis_menu = ctk.CTkOptionMenu(self.filter_frame, values=self.df_columns, variable=self.x_axis, button_color='black', dropdown_hover_color='grey50', button_hover_color='grey50', dropdown_font=self.font2, text_color='yellow2', dropdown_text_color='yellow2', dropdown_fg_color='black', font=self.font2, fg_color='black')
        self.xaxis_menu.grid(row=1, column=0, padx=20, pady=5, sticky='ew')

        self.xaxis_text = ctk.CTkLabel(self.filter_frame, text='Yeti', font=self.font2, text_color='grey50', bg_color='grey18')
        self.xaxis_text.grid(row=0, column=1, padx=20, pady=1, sticky='nsew')
        self.filter1_menu = ctk.CTkOptionMenu(self.filter_frame, values=self.yeti_list, variable=self.yeti_selection, button_color='black', dropdown_hover_color='grey50', button_hover_color='grey50', dropdown_font=self.font2, text_color='yellow2', dropdown_text_color='yellow2', dropdown_fg_color='black', font=self.font2, fg_color='black')
        self.filter1_menu.grid(row=1, column=1, padx=20, pady=5, sticky='ew')

        self.xaxis_text = ctk.CTkLabel(self.filter_frame, text='Load', font=self.font2, text_color='grey50', bg_color='grey18')
        self.xaxis_text.grid(row=0, column=2, padx=20, pady=1, sticky='nsew')
        self.filter2_menu = ctk.CTkOptionMenu(self.filter_frame, values=self.output_list, variable=self.output_selection, button_color='black',dropdown_hover_color='grey50', button_hover_color='grey50', dropdown_font=self.font2, text_color='yellow2', dropdown_text_color='yellow2', dropdown_fg_color='black', font=self.font2, fg_color='black')
        self.filter2_menu.grid(row=1, column=2, padx=20, pady=5, sticky='ew')

        self.xaxis_text = ctk.CTkLabel(self.filter_frame, text='Cycle', font=self.font2, text_color='grey50', bg_color='grey18')
        self.xaxis_text.grid(row=0, column=3, padx=20, pady=1, sticky='nsew')
        self.filter3_menu = ctk.CTkOptionMenu(self.filter_frame, values=self.cycle_list, variable=self.cycle_selection, button_color='black',dropdown_hover_color='grey50', button_hover_color='grey50', dropdown_font=self.font2, text_color='yellow2', dropdown_text_color='yellow2', dropdown_fg_color='black', font=self.font2, fg_color='black')
        self.filter3_menu.grid(row=1, column=3, padx=20, pady=5, sticky='ew')

        self.update_button = ctk. CTkButton(self.filter_frame, corner_radius=5, fg_color='yellow2', text='UPDATE', font=self.font1, text_color='grey18', hover_color='grey50', command=self.drop_filter_data)
        self.update_button.grid(row=0, rowspan=2, column=4, padx=20, pady=10, sticky='nsew')


        # Summary Frame
        self.summary_frame = ctk.CTkScrollableFrame(self, width=250, label_text='SUMMARY', label_font=self.font1, label_fg_color='yellow2', label_text_color='grey18', corner_radius=0, bg_color='black', fg_color='grey18')
        self.summary_frame.grid(row=0, column=2, rowspan=3, padx=5, pady=5, sticky='nsew')
        self.summary_frame.grid_columnconfigure(1, weight=1)

        
        # Report Frame
        self.report_frame = ctk.CTkFrame(self, corner_radius=0, bg_color='black', fg_color='grey18')
        self.report_frame.grid(row=3, column=2, padx=5, pady=5, sticky='nsew')


    def on_move(self,event, b_c = None):
        # no idea why but for somereason I cannot connect mouse movement directly to b_c.on_mouse_move, so this function just passes the event to it
        if self.crosshair_state.get():
            b_c.on_mouse_move(event)


    def import_file(self):
        try:
            ### need to add function to buttons so you cannot select both mixed import and fridgeplexor_imnport

            if self.fridgeplexor_import_state.get(): # if you want to import both Mdata and Ydata and then merge them into full_df
                filename1 = tk.filedialog.askopenfilename(title = "Select Mdata",
                                                        filetypes = [('CSV files', '*.csv')])
                self.text_filepath1.set(f'File_1: {filename1[-30:]}')

                filename2 = tk.filedialog.askopenfilename(title = "Select Ydata",
                                                    filetypes = [('CSV files', '*.csv')])
                self.text_filepath2.set(f'File_1: {filename2[-30:]}')

                with open(filename2, 'r+') as file:
                    reader = csv.reader(file)
                    association_str = next(reader)[0]           # a string which contains the information about the connections of the system, which meters were connected to which yeti's
                    associations = ast.literal_eval(association_str)        
                    associations = {key: associations[key][1] for key in associations}


                Mdata_df = pd.read_csv(filename1, index_col=False)
                Ydata_df = pd.read_csv(filename2, index_col=False, skiprows=1)
                Ydata_df['M_ID'] = Ydata_df['mac'].map(associations)    # add M_ID to the yeti dataframe based on associations, so that it can be merged on later. 
                self.full_df = Mdata_df.merge(Ydata_df, on=['M_ID', 'packet_num'], how='inner', copy=False)

                drop_columns = [c for c in self.full_df.columns if (self.full_df.dtypes[c] == 'object') and (c not in ['mac', 'channel', 'cycle'])] + ['Unnamed: 0_x', 'Unnamed: 0_y', 'packet_num']

            
            elif self.mixed_import_state.get():


                # merge two dataframes from diffrent scripts, two mappls scripts, mappl + serial, serial + serial, etc. May have mixed frequencies, so merge on E_Time
                filename1 = tk.filedialog.askopenfilename(title = "Dataset_1",
                                                        filetypes = [('CSV files', '*.csv')])
                self.text_filepath1.set(f'File_1: {filename1[-30:]}')

                filename2 = tk.filedialog.askopenfilename(title = "Dataset_2",
                                                    filetypes = [('CSV files', '*.csv')])
                self.text_filepath2.set(f'File_2: {filename2[-30:]}')

                filenames = [filename1, filename2]
                dataframes = []

                for filename in filenames:
                    new_df = pd.read_csv(filename)

                    if 'M_ID' in new_df.columns:
                        filtered_dfs = []
                        unique_meters = new_df['M_ID'].unique()
                        for meter in unique_meters:
                            filtered_frame = new_df[new_df['M_ID'] == meter].drop(columns=['M_ID', 'Unnamed: 0'])
                            filtered_frame.columns = [f'{col} {str(meter)}' for col in filtered_frame.columns if col not in ('Time', 'Epoch_Time')] + ['Time', 'Epoch_Time']
                            filtered_dfs += [filtered_frame]

                        new_df = reduce(lambda left, right: pd.merge(left, right, on=['Time', 'Epoch_Time']), filtered_dfs)

                    dataframes.append(new_df)

                #combine the dataframes here after deleting redundant time columns, and some more weird columns before merging
                for df in dataframes:
                    c_set = set(df.columns)
                    drop_set = set(['Time', 'Unnamed: 0'])
                    df.drop(columns=list(c_set.intersection(drop_set)), inplace=True)
                    

                self.full_df = dataframes[0].merge(dataframes[1], on='Epoch_Time', how='outer', suffixes=('_File_1', '_File_2'))
                #drop columns and conditional logic here
                drop_columns = [c for c in self.full_df.columns if (self.full_df.dtypes[c] == 'object')]

            else: # if you dont want to merge, and you already have a good df, either from serial logger, previous merge, etc.
                filename1 = tk.filedialog.askopenfilename(initialdir = "/",
                                                    title = "Select a File",
                                                    filetypes = [('CSV files', '*.csv')])

                self.text_filepath1.set(f' File: {filename1[-25:]}')
                self.full_df = pd.read_csv(filename1)
                if 'M_ID' in self.full_df.columns:
                    filtered_dfs = []
                    unique_meters = self.full_df['M_ID'].unique()
                    for meter in unique_meters:
                        filtered_frame = self.full_df[self.full_df['M_ID'] == meter].drop(columns=['M_ID', 'Unnamed: 0'])
                        filtered_frame.columns = [f'{col} {str(meter)}' for col in filtered_frame.columns if col not in ('Time', 'Epoch_Time')] + ['Time', 'Epoch_Time']
                        filtered_dfs += [filtered_frame]

                    self.full_df = reduce(lambda left, right: pd.merge(left, right, on=['Time', 'Epoch_Time']), filtered_dfs)

                drop_columns = [c for c in self.full_df.columns if (self.full_df.dtypes[c] == 'object')] #if the colum has mixed datatypes, we drop it, gets ride of weird columns in serial logger data
                if 'Unnamed: 0' in self.full_df.columns:
                    drop_columns.append('Unnamed: 0')

            self.disabled_button = None

            try:
                self.yeti_list = [str(y) for y in self.full_df['mac'].unique()]
                self.yeti_selection = ctk.StringVar()
                self.output_list = [str(o) for o in self.full_df['channel'].unique()]
                self.output_selection = ctk.StringVar()
                self.cycle_list = [str(c) for c in self.full_df['cycle'].unique()] + ['All']
                self.cycle_selection = ctk.StringVar()

            except (KeyError, ValueError):
                self.yeti_list = []
                self.output_list = []
                self.cycle_list = []
                self.yeti_selection.set('')
                self.cycle_selection.set('')
                self.output_selection.set('')

            self.full_df = self.full_df.drop(columns=drop_columns, axis=1)
            self.df_columns = self.full_df.columns


            self.parameter_selections = {}
            for c in self.full_df.columns:
                if c not in ['mac', 'channel', 'cycle']:
                    self.parameter_selections[c] = ctk.BooleanVar()
            
            self.init_frames()

            if self.mixed_import_state.get():
                self.export_button.configure(state='normal', fg_color='yellow2')        #allow export of dataset
            else:
                self.x_axis.set('')

        except FileNotFoundError as err:
            print(err)


    def drop_filter_data(self):
        # filters master dataframe based on the slections of the filter dropdowns
        if self.disabled_button is not None:
            self.parameter_switches[self.disabled_button].configure(state='normal')

        self.parameter_selections[self.x_axis.get()].set(False)
        self.parameter_switches[self.x_axis.get()].configure(state='disabled')
        self.disabled_button = self.x_axis.get() # save the most recently disabled buttons name as a variable

        try:
            if self.yeti_selection.get() and self.output_selection.get() and self.cycle_selection.get(): # if filters selections are made, filter. Note 'All' must be selected if you do not want to be filter by that column
                
                if self.cycle_selection.get() == 'All':
                    filtered_df = self.full_df.query(f'mac == "{self.yeti_selection.get()}" and channel == "{self.output_selection.get()}"')
                    filtered_df = filtered_df.drop(labels=['mac', 'channel'], axis=1)
                else:
                    filtered_df = self.full_df.query(f'mac == "{self.yeti_selection.get()}" and channel == "{self.output_selection.get()}" and cycle == {self.cycle_selection.get()}')
                    filtered_df = filtered_df.drop(labels=['mac', 'channel', 'cycle'], axis=1)

                self.filtered_df = filtered_df.sort_values(self.x_axis.get())
                self.update_graph()
            else:
                self.filtered_df = self.full_df
                self.update_graph()
            
        except SyntaxError as err:
            print(err)


    def update_graph(self):
        # updates graph plots from data(remakes plots and draws)
        if self.normalize_state.get():
            dataset = self.normalized_df
        else:
            dataset = self.filtered_df

        self.filtered_frames = {}

        try:
            count = 1

            # clear values from previous plots, reset summary labels
            self.ax1.clear()
            self.current_y_values = {}
            for widget in self.summary_frame.winfo_children():
                widget.destroy()

            # manually make an additional summary label for the x axis value
            selected_x_axis = self.x_axis.get()
            self.current_y_values[selected_x_axis] = ctk.StringVar(value=selected_x_axis)
            data_label = ctk.CTkLabel(self.summary_frame, corner_radius=0, textvariable=self.current_y_values[selected_x_axis], font=self.font2, text_color='grey50')
            data_label.grid(row=0, column=1, padx=5, pady=2, sticky='w')
            text_label= ctk.CTkLabel(self.summary_frame, corner_radius=0, text=f'{selected_x_axis}: ', font=self.font2, text_color='yellow2')
            text_label.grid(row=0, column=0, padx=5, pady=2 , sticky='w')

            # Replot new selected plots, and remake summary labels
            for c in dataset:
                if c != 'cycle':
                    if self.parameter_selections[c].get():

                        # if 'All' cycles is selected, it is a full system import, and we need to break the data into multiple lines for each cycle, and then display them all at once, for each selected parameter
                        if self.cycle_selection.get() == 'All':
                            filtered_frame = dataset.dropna(subset=[f'{c}'])[[selected_x_axis, f'{c}', 'cycle']]
                            cycles = filtered_frame['cycle'].unique()
                            for cycle in cycles:
                                cycle_name = c + '-' + str(cycle)
                                subset = filtered_frame[filtered_frame['cycle'] == cycle]
                                self.filtered_frames[cycle_name] = subset
                                self.ax1.plot(subset[selected_x_axis], subset[c], label=cycle_name, linewidth=1) #plot the line
                                self.current_y_values[cycle_name] = ctk.StringVar(value=cycle_name)
                                data_label = ctk.CTkLabel(self.summary_frame, corner_radius=0, textvariable=self.current_y_values[cycle_name], font=self.font2, text_color='grey50')
                                data_label.grid(row=count, column=1, padx=5, pady=2, sticky='w')
                                text_label= ctk.CTkLabel(self.summary_frame, corner_radius=0, text=f'{cycle_name}: ', font=self.font2, text_color='yellow2', justify='left', wraplength=150)
                                text_label.grid(row=count, column=0, padx=5, pady=2 , sticky='w')
                                count += 1
                        else:
                            # 'All' is not selected and we plot normally
                            filtered_frame = dataset.dropna(subset=[f'{c}'])[[selected_x_axis, f'{c}']]
                            self.filtered_frames[c] = filtered_frame
                            self.ax1.plot(filtered_frame[selected_x_axis], filtered_frame[c], label=c, linewidth=1) #plot the line
                            self.current_y_values[c] = ctk.StringVar(value=c)
                            data_label = ctk.CTkLabel(self.summary_frame, corner_radius=0, textvariable=self.current_y_values[c], font=self.font2, text_color='grey50')
                            data_label.grid(row=count, column=1, padx=5, pady=2, sticky='w')
                            text_label= ctk.CTkLabel(self.summary_frame, corner_radius=0, text=f'{c}: ', font=self.font2, text_color='yellow2', justify='left', wraplength=150)
                            text_label.grid(row=count, column=0, padx=5, pady=2 , sticky='w')
                            count += 1

            if count > 1: # only draw legend if there are actualy plots, if no plots selected count = 0
                self.ax1.legend()

            self.lines = self.ax1.get_lines()
            self.canvas1.draw()

        except (AttributeError, TypeError) as err:
            print(err)




    def mouse_event(self, event):
        self.highlight(event)

        if self.crosshair_state.get():
            self.crosshair_click(event)

        
    def highlight(self, event):
        if hasattr(self, 'ax1'):
            legend = self.ax1.get_legend()
            if legend:
                if legend.contains(event)[0]:
                    highlights = {}
                    texts = legend.get_texts()
                    for i, text in enumerate(texts): # determine if a line needs highlighting, based on click location
                        if text.contains(event)[0]:
                            highlights[i] = True

                    if highlights:  # there is a line that needs to be highlighted, highlight it, and dim the rest
                        for i, text in enumerate(texts):
                            if i in highlights:
                                self.lines[i].set_alpha(1)
                                self.lines[i].set_linewidth(1.5)
                                text.set_color('yellow')
                            else:
                                self.lines[i].set_alpha(.3)
                                self.lines[i].set_linewidth(1)
                                text.set_color('white')
                    else:   # if there are no valid highlights(aka you clicked in the legend, but not on a line text, then return all lines to normal)
                        for i, text in enumerate(texts):       
                            self.lines[i].set_alpha(1)
                            self.lines[i].set_linewidth(1)
                            text.set_color('white')

                    self.canvas1.draw_idle()

    def crosshair_click(self, event):
        # on click, if crosshair enabled - update summary values to the value of each visible graphs at the nearest x cordinate(snaps to nearest real datapoint)
        raw_x_value = event.xdata

        try:
            self.clicked_hline.remove()

        except (AttributeError, ValueError):
            pass

        try:
            self.scat_plt1.remove()

        except (AttributeError, ValueError):
            pass

        lines = self.lines
        selected_xaxis = self.x_axis.get()

        n = 0
        scat_x_vals = []
        scat_y_vals = []

        for c in self.filtered_df:
            if c != selected_xaxis:
                if c != 'cycle':
                    if self.parameter_selections[c].get():

                        if self.cycle_selection.get() == 'All':
                            for name in self.current_y_values:
                                split_name = name.split('-')
                                if c == split_name[0]:
                                    line = lines[n]
                                    x_data, y_data = line.get_data()
                                    n += 1
                                    minvalue_index = np.abs(x_data - raw_x_value).argmin()             #gets the closest x_data point for the clicked x position for each line indiviually

                                    set_values = self.filtered_df.loc[self.filtered_df['cycle'] == int(split_name[1]), [f'{c}', selected_xaxis]]
                                    single_value = set_values.loc[set_values[selected_xaxis] == x_data[minvalue_index], c]
                                    self.current_y_values[name].set(round(single_value.iloc[0], 3))
                                    scat_x_vals.append(x_data[minvalue_index])
                                    scat_y_vals.append(y_data[minvalue_index])

                        else: # is selected, but "All" cyles isn't
                            line = lines[n]
                            x_data, y_data = line.get_data()
                            n += 1
                            minvalue_index = np.abs(x_data - raw_x_value).argmin()             #gets the closest x_data point for the clicked x position for each line indiviually
                            self.current_y_values[c].set(round(self.filtered_df.loc[self.filtered_df[selected_xaxis] == x_data[minvalue_index], f'{c}'].values[0], 3))        # we still get summary frame data directly from the dataframe, so normalization has no effect

                            scat_x_vals.append(x_data[minvalue_index])
                            scat_y_vals.append(y_data[minvalue_index])

            else: # it is x axis
                minvalue_index = np.abs(self.filtered_df[selected_xaxis] - raw_x_value).argmin()
                self.current_y_values[selected_xaxis].set(round(self.filtered_df[selected_xaxis].iloc[minvalue_index], 3))

        self.clicked_hline = self.ax1.axvline(x = raw_x_value, ls='--', color='yellow')
        self.scat_plt1 = self.ax1.scatter(scat_x_vals, scat_y_vals, c='yellow', marker='x', s=60)

        self.canvas1.draw_idle()


    def key_event(self, event):
        # this function manages our custom hotkeys


        ##### -------------------------------------------------------------------------
        if event.key == 'x':
            if self.crosshair_state.get():  # if the crosshair is on, turn it off, set the visibility false and redraw it to remove the cursor from the screen

                self.crosshair_state.set(0)
                need_redraw = self.blitted_cursor1.set_cross_hair_visible(False)

                if need_redraw:
                    self.blitted_cursor1.ax.figure.canvas.restore_region(self.blitted_cursor1.background)
                    self.blitted_cursor1.ax.figure.canvas.blit(self.blitted_cursor1.ax.bbox)

            else:
                self.crosshair_state.set(1)

        #### --------------------------------------------------------------------------
        if event.key == 'n':
            if self.normalize_state.get():
                self.normalize_state.set(0)
            else:
                self.normalize_state.set(1)
                self.normalize_data()

            self.update_graph()

        #### -------------------------------------------------------------------------

    def normalize_data(self):
        if self.normalize_state.get():
    
            offset_df = self.filtered_df.subtract(self.filtered_df.min())

            self.normalized_df = offset_df.apply(lambda x: x.div(x.max()) if x.max() != 0 else x, axis=0)

            for c in self.normalized_df.columns:
                if c in ['cycle', 'mac', 'channel', self.x_axis.get()]: #resets any values we don't want normalized, which are filtering columns and the selected x axis
                    self.normalized_df[c] = self.filtered_df[c]

        self.update_graph()


    def fridgeplexor_import_select(self):
        if self.fridgeplexor_import_state.get():
            self.mixed_import_state.set(0)

    def mixed_import_select(self):
        if self.mixed_import_state.get():
            self.fridgeplexor_import_state.set(0)

    def export_file(self):
        export_filename = Path(tk.filedialog.asksaveasfilename(defaultextension='.csv', title='Save output data as: ', filetypes = [('CSV files', '*csv')]))
        if export_filename.exists():
            export_filename.unlink()

        if self.filtered_df is not None:
            self.filtered_df.to_csv(export_filename, header=True)


if __name__ == '__main__':
    app = APP()
    app.mainloop()