import pandas as pd
import numpy as np
import tkinter as tk
import csv
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.widgets as wdg
import matplotlib.style as mplstyle
import ast
import time
import sys
from functools import reduce

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

# V0.9.1

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
        self.title('PostProcessing Tool')
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
        self.crosshair_state = ctk.IntVar(value=1)
        self.double_import = ctk.IntVar(value=0)
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
        self.import_frame.rowconfigure((0,1,2,3), weight=1)

        self.file_text1 = ctk.CTkLabel(self.import_frame, corner_radius=5, textvariable=self.text_filepath1, fg_color='black', text_color='grey50', font=self.font2, width=250, anchor='w')
        self.file_text1.grid(row=0, column=0, padx=5, pady=[5,0], sticky='new')
        self.file_text2 = ctk.CTkLabel(self.import_frame, corner_radius=5, textvariable=self.text_filepath2, fg_color='black', text_color='grey50', font=self.font2, width=250, anchor='w')
        self.file_text2.grid(row=1, column=0, padx=5, pady=[0,5], sticky='new')

        self.double_import_checkbox = ctk.CTkCheckBox(self.import_frame, text='Import both Mdata and Ydata', corner_radius=5, hover_color='yellow2', fg_color='black',bg_color='grey18', border_color='black', font=self.font2, text_color='grey50', variable=self.double_import)
        self.double_import_checkbox.grid(row=2, column=0, padx=5, pady=5, sticky='new')

        self.import_button = ctk.CTkButton(self.import_frame, corner_radius=5, text='Import File(s)', fg_color='yellow2', text_color='grey18', font=self.font1, command=self.import_file, hover_color='grey50')
        self.import_button.grid(row=3, column=0, padx=10, pady=10, sticky='nsew')
        

        # Parameter Frame
        self.parameter_frame = ctk.CTkScrollableFrame(self, corner_radius=0, label_text='PARAMETERS', label_font=self.font1, label_fg_color='yellow2', label_text_color='grey18', bg_color='black', fg_color='grey18')
        self.parameter_frame.grid(row=2, column=0, padx=5, pady=5, sticky='nsew')

        self.parameter_switches = {}
        for i, p in enumerate(self.parameter_selections):
            switch = ctk.CTkSwitch(self.parameter_frame, text=p, variable=self.parameter_selections[p], command=lambda: self.update_graph(self.filtered_df), font=self.font2, progress_color='yellow2', fg_color='black', button_color='grey50', text_color='grey50', switch_width=40)
            switch.grid(row=i, column=0, padx=15, pady=5, sticky='ew')
            self.parameter_switches[p] = switch


        # Options Frame
        self.options_frame = ctk.CTkFrame(self, corner_radius=0, bg_color='black', fg_color='grey18')
        self.options_frame.grid(row=3, column=0, padx=5, pady=5, sticky='nsew')
        self.options_frame.columnconfigure(0, weight=1)

        self.options_header = ctk.CTkLabel(self.options_frame, corner_radius=0, fg_color='yellow2', text_color='grey18', text='OPTIONS', font=self.font1)
        self.options_header.grid(row=0, column=0, padx=0, pady=0, sticky='nsew')

        self.normalized_button = ctk.CTkButton(self.options_frame, text='Normalize', corner_radius=5, fg_color='yellow2', font=self.font1, text_color='grey18', hover_color='grey50', command=self.normalize_data)
        self.normalized_button.grid(row=1, column=0, padx=5, pady=(10,5), sticky='nsew' )

        self.crosshair_checkbox = ctk.CTkCheckBox(self.options_frame, text='Crosshair', corner_radius=5, hover_color='yellow2', fg_color='black',bg_color='grey18', border_color='black', font=self.font2, text_color='grey50', variable=self.crosshair_state)
        self.crosshair_checkbox.grid(row=2, column=0, padx=5, pady=5, sticky='nsew' )

        #self.force_close_button = ctk.CTkButton(self.options_frame, text='Force Close', corner_radius=5, fg_color='yellow2', font=self.font1, text_color='grey18', hover_color='grey50', command=lambda: _quit(self))
        #self.force_close_button.grid(row=2, column=0, padx=5, pady=5, sticky='nsew' )



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
            if self.double_import.get(): # if you want to import both Mdata and Ydata and then merge them into full_df
                filename1 = tk.filedialog.askopenfilename(title = "Select Mdata",
                                                        filetypes = [('CSV files', '*.csv')])
                self.text_filepath1.set(f' File(s): {filename1[-25:]}')

                filename2 = tk.filedialog.askopenfilename(title = "Select Ydata",
                                                    filetypes = [('CSV files', '*.csv')])
                self.text_filepath2.set(f'{filename2[-30:]}')

                with open(filename2, 'r+') as file:
                    reader = csv.reader(file)
                    association_str = next(reader)[0]
                    associations = ast.literal_eval(association_str)
                    associations = {key: associations[key][1][0] for key in associations}


                Mdata_df = pd.read_csv(filename1, index_col=False)
                Ydata_df = pd.read_csv(filename2, index_col=False, skiprows=1)
                Ydata_df['M_ID'] = Ydata_df['Yeti_ID'].map(associations)
                self.full_df = Mdata_df.merge(Ydata_df, on=['M_ID', 'packet_num'], how='inner', copy=False)

                drop_columns = [c for c in self.full_df.columns if (self.full_df.dtypes[c] == 'object') and (c not in ['yeti_ID', 'channel', 'cycle'])]
                
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
                        print(filtered_frame.columns)
                        filtered_frame.columns = [f'{col} {str(meter)}' for col in filtered_frame.columns if col != 'timestamp'] + ['timestamp']
                        filtered_dfs += [filtered_frame]

                    self.full_df = reduce(lambda left, right: pd.merge(left, right, on='timestamp'), filtered_dfs)

            drop_columns = [c for c in self.full_df.columns if (self.full_df.dtypes[c] == 'object')] #if the colum has mixed datatypes, we drop it, gets ride of weird columns in serial logger data
            self.disabled_button = None
            self.x_axis.set('')

            try:
                self.yeti_list = [str(y) for y in self.full_df['Yeti_ID'].unique()]
                self.yeti_selection = ctk.StringVar()
                self.output_list = [str(o) for o in self.full_df['channel'].unique()]
                self.output_selection = ctk.StringVar()
                self.cycle_list = [str(c) for c in self.full_df['cycle'].unique()]
                self.cycle_selection = ctk.StringVar()

            except (KeyError, ValueError):
                self.yeti_list = []
                self.output_list = []
                self.cycle_list = []
                self.yeti_selection.set('')
                self.cycle_selection.set('')
                self.output_selection.set('')

            self.full_df = self.full_df.drop(drop_columns, axis=1)
            self.df_columns = self.full_df.columns

            self.parameter_selections = {}
            for c in self.full_df.columns:
                if c not in ['Yeti_ID', 'channel', 'cycle']:
                    self.parameter_selections[c] = ctk.BooleanVar()
            
            self.init_frames()

        except FileNotFoundError as err:
            print(err)


    def drop_filter_data(self):
        # filters master dataframe based on the slections of the filter dropdowns
        if self.disabled_button is not None:
            self.parameter_switches[self.disabled_button].configure(state='normal')

        self.parameter_selections[self.x_axis.get()].set(False)
        self.parameter_switches[self.x_axis.get()].configure(state = 'disabled')
        self.disabled_button = self.x_axis.get() # save the most recently disabled buttons name as a variable

        try:
            if self.yeti_selection.get() and self.output_selection.get() and self.cycle_selection.get(): # if filters selections are made, filter. Note 'All' must be selected if you do not want to be filter by that column
                filtered_df = self.full_df.query(f'Yeti_ID == "{self.yeti_selection.get()}" and channel == {self.output_selection.get()} and cycle == {self.cycle_selection.get()}')
                filtered_df = filtered_df.drop(labels=['Yeti_ID', 'channel', 'cycle'], axis=1)
                self.filtered_df = filtered_df
                self.update_graph(filtered_df)
            else:
                self.filtered_df = self.full_df
                self.update_graph(self.full_df)
            
        except SyntaxError as err:
            print(err)


    def update_graph(self, dataset):
        # updates graph plots from data(remakes plots and draws)

        try:
            count = 1
            df = dataset.sort_values(self.x_axis.get(), ignore_index=True)

            # clear values from previous plots, reset summary labels
            self.ax1.clear()
            self.current_y_values = {}
            for widget in self.summary_frame.winfo_children():
                widget.destroy()

            # manually make an additional label for the x axis value
            self.current_y_values[self.x_axis.get()] = ctk.StringVar(value=self.x_axis.get())
            data_label = ctk.CTkLabel(self.summary_frame, corner_radius=0, textvariable=self.current_y_values[self.x_axis.get()], font=self.font2, text_color='grey50')
            data_label.grid(row=0, column=1, padx=5, pady=2, sticky='w')
            text_label= ctk.CTkLabel(self.summary_frame, corner_radius=0, text=f'{self.x_axis.get()}: ', font=self.font2, text_color='yellow2')
            text_label.grid(row=0, column=0, padx=5, pady=2 , sticky='w')

            # Replot new selected plots, and remake summary labels
            for c in df:
                print(c)
                if self.parameter_selections[c].get():
                    lines = self.ax1.plot(df[self.x_axis.get()], df[c], label=c, linewidth=1) #plot the line
                    self.current_y_values[c] = ctk.StringVar(value=c)
                    data_label = ctk.CTkLabel(self.summary_frame, corner_radius=0, textvariable=self.current_y_values[c], font=self.font2, text_color='grey50')
                    data_label.grid(row=count, column=1, padx=5, pady=2, sticky='w')
                    text_label= ctk.CTkLabel(self.summary_frame, corner_radius=0, text=f'{c}: ', font=self.font2, text_color='yellow2', justify='left', wraplength=150)
                    text_label.grid(row=count, column=0, padx=5, pady=2 , sticky='w')
                    count += 1

            if count != 0: # only draw legend if there are actualy plots, if no plots selected count = 0
                self.ax1.legend()

            self.canvas1.draw()

        except (AttributeError, TypeError) as err:
            print(err)

    
    def mouse_event(self, event):
        # on click, update summary values to the value of each visible graphs at the nearest x cordinate(snaps to nearest real datapoint)
        raw_x_value = event.xdata
        minvalue_index = np.abs(self.filtered_df[self.x_axis.get()] - raw_x_value).argmin()
        for c in self.filtered_df:
            if c != self.x_axis.get():
                if self.parameter_selections[c].get():
                    self.current_y_values[c].set(f'{self.filtered_df[c].iloc[minvalue_index]}')
            else:
                self.current_y_values[self.x_axis.get()].set(self.filtered_df[self.x_axis.get()].iloc[minvalue_index])
        try:
            self.clicked_hline.remove()
        except AttributeError:
            pass

        self.clicked_hline = self.ax1.axvline(x = self.filtered_df[self.x_axis.get()].iloc[minvalue_index], ls='--', color='yellow')
        self.canvas1.draw()


    def key_event(self, event):
        # this function manages our custom hotkeys
        pass


    def normalize_data(self):
        column_mins = self.filtered_df.min()
        offset_df = (self.filtered_df - column_mins ) # subtracts each columns minimum value to fit them all around 0
        offset_df_max = offset_df.max()
        normalized_df = offset_df / offset_df_max
        normalized_df[self.x_axis.get()] = self.filtered_df[self.x_axis.get()] # reset the Time column as we don't want it normalized
        self.update_graph(normalized_df)

    
if __name__ == '__main__':
    app = APP()
    app.mainloop()