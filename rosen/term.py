import curses
import curses.textpad
import time
import datetime
import os

def trim_nulls(bstring):

    if len(bstring) == 0:
        return ''
    place = len(bstring) - 1

    while place >= 0 and bstring[place] == 32:
        place = place - 1

    return bstring[:place + 1]

class Console:

    def __init__(self, splash_art=None, debug=False):
        self.stdscr = None # Main screen
        self.inputw = None # Terminal input
        self.statusw = None # System status
        self.telw = None # Feed of added lines
        self.time = True # False for no UNIX timestamps
        self.cmdf = None # Function to pass commands to. Should return -1 for err
        self.logfile = None
        self.cursor_pos = [0,0]
        self.history = ['']
        self.hist_pos = 0
        self.output_hist = []
        self.lines_locked = False
        self.old_LINES = 0
        self.old_COLS = 0
        self.splash_art = splash_art
        self.debug_enable = debug

        try:
            homepath = os.environ["HOME"]
            with open(homepath+'/.seaque_history', 'r') as histf:
                for l in histf.readlines():
                    self.history.append(l[:-1])
        except FileNotFoundError:
            pass

        # Clear debug log
        if self.debug_enable:
            with open('debugf.txt', 'w') as f:
                f.close()

        self.debug_log("Init Done")

    def debug_log(self, string):

        if not self.debug_enable:
            return
        with open('debugf.txt', 'a') as debugf:
            debugf.write(string + '\n')
            debugf.flush()

    def redraw(self):
        curses.update_lines_cols()

        self.stdscr.resize(curses.LINES, curses.COLS)
        self.inputw.resize(1, curses.COLS-2)
        self.telw.resize(curses.LINES-2, curses.COLS-22)
        self.statusw.resize(curses.LINES-2, 20)


        self.inputw.mvwin(curses.LINES-1, 2)
        self.statusw.mvwin(0, curses.COLS-20)
       


        self.inputw.redrawwin()
        self.statusw.redrawwin()

        # Draw borders
        for i in range(curses.COLS):
            self.stdscr.addch(curses.LINES-2, i, curses.ACS_HLINE, curses.color_pair(5))
        for i in range(curses.LINES-1):
            self.stdscr.addch(i, curses.COLS-21, curses.ACS_VLINE, curses.color_pair(5))
        self.stdscr.addch(curses.LINES-2, curses.COLS-21, curses.ACS_BTEE, curses.color_pair(5))


        self.stdscr.addstr(curses.LINES-1, 0, '> ')
        self.inputw.move(self.cursor_pos[0], self.cursor_pos[1])

        self.telw.erase()
        self.lines_locked = False
        old_out_hist = self.output_hist
        self.output_hist = []
        for l in old_out_hist:
            self.add_line(l[1], time_t=l[0])
        self.lines_locked = True

        self.telw.redrawwin()

        self.stdscr.refresh()
        self.inputw.refresh()
        self.telw.refresh()
        self.statusw.refresh()

    def start(self, cmdf=None, debug=False, logfile='__default__'):

        # Setting debug echos unknown/unhandled key codes for debugging
        # Set vars
        self.cmdf = cmdf
        homedir = os.environ['HOME']

        if logfile == '__default__':
            if os.access(homedir+'/seaque_logs', os.F_OK) is False:
                os.mkdir(homedir+'/seaque_logs')

            self.logfile = open(homedir+'/seaque_logs/log_' + datetime.date.today().isoformat() + '.txt', 'a')
        else:
            self.logfile = open(logfile, 'a')

        # Boilerplate
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        self.stdscr.clear()

        # Get colors working
        curses.start_color()
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)

        self.debug_log("Drawing Splash")
        # Draw splash screen
        if self.splash_art is not None:
            self.display_splash()

        self.debug_log("Done with Splash")

        # Note: for dumb reasons, curses can't just write to the bottom right
        # corner with addch, need insch
        self.inputw = curses.newwin(1, curses.COLS - 2, curses.LINES-1, 2)
        self.statusw = curses.newwin(curses.LINES-2, 20, 0, curses.COLS-20)
        self.telw = curses.newwin(curses.LINES-2, curses.COLS-22, 0, 0)
        self.telw.scrollok(True)

        self.debug_log(f'Initialized: {curses.LINES}, {curses.COLS}')
        self.old_LINES = curses.LINES
        self.old_COLS = curses.COLS
        # Draw borders
        for i in range(curses.COLS):
            self.stdscr.addch(curses.LINES-2, i, curses.ACS_HLINE, curses.color_pair(5))
        for i in range(curses.LINES-1):
            self.stdscr.addch(i, curses.COLS-21, curses.ACS_VLINE, curses.color_pair(5))
        self.stdscr.addch(curses.LINES-2, curses.COLS-21, curses.ACS_BTEE, curses.color_pair(5))

        # Prompt
        self.stdscr.addstr(curses.LINES-1, 0, '> ')

        # Update screens
        self.stdscr.refresh()
        self.statusw.refresh()
        self.telw.refresh()
        self.inputw.move(self.cursor_pos[0], self.cursor_pos[1])
        self.inputw.refresh()

        # Input handling
        length = 0
        while True:

            try:
                ch = self.stdscr.getkey()
            except KeyboardInterrupt:
                return

            while self.lines_locked is True:
                pass

            self.lines_locked = True

            # ASCII character input
            if (len(ch) == 1 and 31 < ord(ch) < 126):
                self.inputw.insch(*self.cursor_pos, ch)
                self.cursor_pos[1] = self.cursor_pos[1] + 1
                self.inputw.move(*self.cursor_pos)
                length = length + 1
            # Backspace
            elif ch in (curses.KEY_BACKSPACE, 'KEY_BACKSPACE') and self.cursor_pos[1] != 0:
                self.cursor_pos[1] = self.cursor_pos[1] - 1
                self.inputw.delch(*self.cursor_pos)
                self.inputw.move(*self.cursor_pos)
                length = length - 1
            elif ch == '\x15':
                while self.cursor_pos[1] != 0:
                    self.cursor_pos[1] = self.cursor_pos[1] - 1
                    self.inputw.delch(*self.cursor_pos)
                    self.inputw.move(*self.cursor_pos)
                    length = length - 1
            # Left arrow key
            elif ch == 'KEY_LEFT' and self.cursor_pos[1] != 0:
                self.cursor_pos[1] = self.cursor_pos[1] - 1
                self.inputw.move(*self.cursor_pos)
            # Right arrow key
            elif ch == 'KEY_RIGHT' and self.cursor_pos[1] != length:
                self.cursor_pos[1] = self.cursor_pos[1] + 1
                self.inputw.move(*self.cursor_pos)
            # Enter, calls cmdf with buffer content
            elif ch in ('KEY_ENTER', '\n', ch == '\r'):
                command = self.inputw.instr(0,0)
                string = trim_nulls(command).decode('ascii')
                if string != '':
                    if len(self.history) > 1 and string == self.history[1]:
                        pass
                    else:
                        self.history.insert(1, string)
                        self.history[0] = ''
                self.cursor_pos = [0,0]
                self.hist_pos = 0
                self.inputw.move(*self.cursor_pos)
                self.inputw.clear()
                length = 0
                self.lines_locked = False
                self.add_line( '> ' + string)
                self.lines_locked = True
                if self.cmdf is not None:
                    self.cmdf(string)

            # Up arrow key, goes up in history
            elif ch == 'KEY_UP':
                if self.hist_pos != len(self.history) - 1 and len(self.history) > 1:
                    command = self.inputw.instr(0,0)
                    string = trim_nulls(command).decode('ascii')
                    self.history[self.hist_pos] = string
                    self.hist_pos = self.hist_pos + 1
                    self.inputw.clear()
                    self.inputw.addstr(self.history[self.hist_pos])
                    length = len(self.history[self.hist_pos])
                    self.cursor_pos[1] = length
                    self.inputw.move(*self.cursor_pos)

            # Down arrow key, down in history
            elif ch == 'KEY_DOWN':
                if self.hist_pos != 0:
                    command = self.inputw.instr(0,0)
                    string = trim_nulls(command).decode('ascii')
                    self.history[self.hist_pos] = string
                    self.hist_pos = self.hist_pos - 1
                    self.inputw.clear()
                    self.inputw.addstr(self.history[self.hist_pos])
                    length = len(self.history[self.hist_pos])
                    self.cursor_pos[1] = length
                    self.inputw.move(*self.cursor_pos)

            # Home key, move to beginning of text
            elif ch == 'KEY_HOME':
                self.cursor_pos = [0,0]
                self.inputw.move(*self.cursor_pos)

            # End key, go to end of text
            elif ch == 'KEY_END':
                self.cursor_pos = [0,length]
                self.inputw.move(*self.cursor_pos)

            # Handle resize
            elif ch == 'KEY_RESIZE':
                self.redraw()

            # Ctrl+D to exit
            elif ch == '\x04':
                if length == 0:
                    return

            # If debug is set, output any unhandled keys to the terminal
            # This helps with identifying new keys to be added
            elif debug:
                self.lines_locked = False
                self.add_line(str(ch.encode('ascii')))
                self.lines_locked = True

            # Refresh
            self.inputw.refresh()
            self.lines_locked = False

    def cleanup(self):
        homepath = os.environ["HOME"]
        with open(homepath+'/.seaque_history', 'w') as histf:
            for i,l in enumerate(self.history[1:]):
                if i > 5000:
                    break
                histf.write(l + '\n')

        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def display_splash(self):
        #with open(self.splash_art, 'r') as splash_file:
        #    lines = splash_file.readlines()

        lines = self.splash_art.split('\n')
        dimy = len(lines)
        dimx = len(lines[0]) # Assume all lines padded

        self.debug_log(f'Splash is {dimy} by {dimx}')

        # Skip splash if it won't fit
        if dimy > (curses.LINES - 1) or dimx > (curses.COLS - 1):
            return

        # Center image

        startx = round((curses.COLS - dimx) / 2.0)
        starty = round((curses.LINES - dimy) / 2.0)



        self.stdscr.move(starty, startx)

        for i in range(dimy):
            self.stdscr.move(starty+i, startx)
            self.stdscr.addstr(lines[i])

        self.stdscr.refresh()

        time.sleep(.5)

        self.stdscr.clear()


    def add_line(self, string, time_t=0):

        while self.lines_locked == True:
            pass

        if time_t == 0:
            time_t = time.time()

        self.lines_locked = True
        old_cursor_pos = self.cursor_pos

        self.output_hist.append((time_t,string))
        self.output_hist = self.output_hist[len(self.output_hist)-300:]


        maxw = self.telw.getmaxyx()[1]-1
        length = len(string)
        pos = 0

        # Log
        if self.logfile is not None:
            self.logfile.write(str(time_t) + ':' +  string + '\n')
            self.logfile.flush()

        # Put all lines up by one
        self.telw.scroll(1)


        if self.time is True:
            times = str(int(time_t))+': '
            self.telw.addstr(curses.LINES-3, 0, times, curses.color_pair(3))
            self.telw.addstr(curses.LINES-3, len(times), string[:(maxw-len(times))])
            length = length - (maxw-len(times))
            pos = maxw-len(times)
        else:
            self.telw.addstr(curses.LINES-3, 0, string[:maxw])
            length = length - maxw
            pos = maxw

        while length > 0:
            self.telw.scroll(1)
            self.telw.addstr(curses.LINES-3, 0, string[pos:maxw+pos])
            pos = pos + maxw
            length = length - maxw

        self.inputw.move(*old_cursor_pos)
        self.telw.refresh()
        self.inputw.refresh()

        self.lines_locked = False

