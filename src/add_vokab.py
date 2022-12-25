import curses
import npyscreen
from vokab import Vokab
from leo import search
import logging
import re
import datetime

today = datetime.datetime.now()
logging.basicConfig(filename=f"../log/{today:%Y_%m_%d__%H_%M_%S}.log",
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class VokabApp(npyscreen.NPSAppManaged):
    def __init__(self, vokab):
        self.vokab = vokab
        super().__init__()

    def onStart(self):
        self.registerForm("MAIN", VokabForm(vokab))


class VokabForm(npyscreen.FormBaseNew):
    def __init__(self, vokab, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prev_term = None
        self.vokab = vokab
        self.section_index = 0

    def create(self):
        self.query = self.add(npyscreen.TitleText, name="Search:")
        self.choices = self.add(
                npyscreen.TitleMultiSelect,
                value=[],
                name=f"1234567890123",
                values=[],
                scroll_exit=True,
                hidden=True,
            )
        self.choices.entry_widget.handlers[curses.KEY_PPAGE] = self.h_prev_section
        self.choices.entry_widget.handlers[curses.KEY_NPAGE] = self.h_next_section
        self.choices.entry_widget.handlers[ord('k')] = self.h_editing_done

    def afterEditing(self):
        self.vokab.add(self.filtered_results)
        self.parentApp.setNextForm(None)

    def update_results(self):
        if self.term == self.prev_term or self.term.strip() == "":
            return
        self.prev_term = self.term
        self.results = search(self.term)
        self.section_names = list(self.results)
        self.section_index = 0
        self.filtered_results = {}

    def update_choices(self):
        if self.term.strip() == "":
            return
        if not self.section_names:
            self.choices.label_widget.value = "no result"
            self.choices.set_values([])
            return

        logger.info("update_choices ...")
        self.section_index %= len(self.results)
        section_name = self.section_names[self.section_index]
        section_content = self.results[section_name]
        self.choices.label_widget.value = section_name
        maxi = max(len(line['de']) for line in section_content)
        self.choices.set_values([
            f"{line['de'].ljust(maxi)}  -  {line['fr']}"
            for line in section_content
        ])
        self.choices.value = [
            i for i, content in enumerate(self.results[section_name])
            if section_name in self.filtered_results and content in self.filtered_results[section_name]
        ]
        self.choices.hidden = False
        self.choices.update()
        logger.info("update_choices ... done")

    def update_filtered_results(self):
        if self.term.strip() == "":
            return
        if not self.section_names:
            self.filtered_results = {}
            return

        logger.info("update_filtered_results ...")
        section_name = self.section_names[self.section_index]
        self.filtered_results[section_name] = [
            self.results[section_name][i] for i in self.choices.value
        ]
        if not self.choices.value:
            self.filtered_results.pop(section_name)
        logger.info(str(self.filtered_results))
        logger.info("update_filtered_results ... done")

    def while_editing(self, widget):
        self.term = self.query.value.strip()

        self.update_results()
        self.update_filtered_results()
        self.update_choices()

    def set_up_handlers(self):
        super().set_up_handlers()
        self.handlers[curses.KEY_NPAGE] = self.h_next_section
        self.handlers[curses.KEY_PPAGE] = self.h_prev_section
        self.handlers[ord('k')] = self.h_editing_done

    def h_editing_done(self, arg):
        self.editing = False
        self.update_filtered_results()
        self.parentApp.switchForm(None)

    def h_next_section(self, arg):
        self.update_filtered_results()
        self.section_index += 1
        self.section_index %= len(self.results)
        self.update_choices()

    def h_prev_section(self, arg):
        self.update_filtered_results()
        self.section_index -= 1
        if self.section_index < 0: self.section_index = len(self.results) - 1
        self.update_choices()


def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'a').close()


if __name__ == "__main__":
    import shutil
    import os

    root = '../data'
    filename = "vokab.md"
    filepath = f'{root}/{filename}'
    files = [x for x in os.listdir(root) if re.match(f"{filename}\.[0-9]+", x)]
    next_int = max([0] + [int(re.match(f"{filename}\.([0-9]+)", x).group(1)) for x in files]) + 1

    touch(filepath)

    with open(filepath, 'r') as f:
        vokab = Vokab(f)

    shutil.copyfile(filepath, filepath + f'.{next_int:06d}')

    App = VokabApp(vokab)
    App.run()

    with open(filepath, 'w') as f:
        vokab.to_file(f)