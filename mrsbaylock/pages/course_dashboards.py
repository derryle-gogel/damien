"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

import itertools
import re
import time

from flask import current_app as app
from mrsbaylock.pages.damien_pages import DamienPages
from mrsbaylock.test_utils import utils
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait as Wait


class CourseDashboards(DamienPages):
    EVALUATION_ROW = (By.XPATH, '//tr[contains(@class, "evaluation-row")]')
    EVALUATION_STATUS = (By.XPATH, '//td[contains(@id, "-status")]')
    NO_SECTIONS_MGS = (By.XPATH, '//span[text()="No eligible sections to load."]')

    @staticmethod
    def eval_row_xpath(evaluation):
        ccn = f'td[contains(@id, "courseNumber")][starts-with(., " {evaluation.ccn}")]'

        if evaluation.instructor.uid:
            uid = f'[contains(.,"{evaluation.instructor.uid}")]'
        else:
            uid = '[not(div)]'
        instr = f'following-sibling::td[contains(@id, "instructor")]{uid}'

        form_name = f'[contains(., " {evaluation.dept_form} ")]' if evaluation.dept_form else '[not(text())]'
        dept_form = f'following-sibling::td[contains(@id, "departmentForm")]{form_name}'
        return f'//{ccn}/{instr}/{dept_form}/ancestor::tr'

    def rows_of_evaluation(self, evaluation):
        return self.elements((By.XPATH, self.eval_row_xpath(evaluation)))

    @staticmethod
    def section_row(evaluation):
        return By.XPATH, f'//tr[contains(., "{evaluation.ccn}")]'

    def wait_for_eval_row(self, evaluation):
        time.sleep(1)
        self.wait_for_element((By.XPATH, self.eval_row_xpath(evaluation)), utils.get_medium_timeout())

    def visible_evaluation_rows(self):
        return self.elements(CourseDashboards.EVALUATION_ROW)

    def wait_for_eval_rows(self):
        time.sleep(1)
        Wait(self.driver, utils.get_medium_timeout()).until(
            ec.presence_of_all_elements_located(CourseDashboards.EVALUATION_ROW),
        )
        self.hit_tab()
        self.scroll_to_top()
        time.sleep(2)

    def wait_for_no_sections(self):
        time.sleep(1)
        self.wait_for_element(CourseDashboards.NO_SECTIONS_MGS, utils.get_short_timeout())

    @staticmethod
    def expected_eval_data(evals):
        data = []
        for e in evals:
            dates = ''
            if e.eval_start_date:
                dates = f"{e.eval_start_date.strftime('%m/%d/%y')} - {e.eval_end_date.strftime('%m/%d/%y')}"
            if e.instructor is None or e.instructor.uid is None:
                uid = ''
                name = ''
            else:
                uid = e.instructor.uid.strip()
                name = f'{e.instructor.first_name} {e.instructor.last_name}' if e.instructor.first_name else ''
            listings = e.x_listing_ccns or e.room_share_ccns
            if listings:
                listings.sort()
            data.append(
                {
                    'ccn': e.ccn,
                    'listings': (listings or []),
                    'course': f'{e.subject} {e.catalog_id} {e.instruction_format} {e.section_num}',
                    'uid': uid,
                    'name': name,
                    'form': (e.dept_form or ''),
                    'type': (e.eval_type or ''),
                    'dates': dates,
                },
            )
        return data

    def visible_eval_data(self):
        time.sleep(1)
        data = []
        for el in self.elements(CourseDashboards.EVALUATION_STATUS):
            idx = el.get_attribute('id').split('-')[1]
            uid_loc = (By.XPATH, f'//td[@id="evaluation-{idx}-instructor"]/div')
            uid = ''
            name = ''
            if self.is_present(uid_loc):
                parts = self.element(uid_loc).text.strip().split()
                uid = parts[-1].replace('(', '').replace(')', '')
                name = ' '.join(parts[0:-1])
            listings_loc = (By.XPATH, f'//td[@id="evaluation-{idx}-courseNumber"]/div[@class="xlisting-note"]')
            listings = []
            if self.is_present(listings_loc):
                listings = re.sub('[a-zA-Z(,)-]+', '', self.element(listings_loc).text).strip().split()

            data.append(
                {
                    'ccn': self.element((By.ID, f'evaluation-{idx}-courseNumber')).text.strip().split('\n')[0],
                    'listings': listings,
                    'course': self.element((By.ID, f'evaluation-{idx}-courseName')).text.strip(),
                    'uid': uid,
                    'name': name,
                    'form': self.element((By.ID, f'evaluation-{idx}-departmentForm')).text.strip(),
                    'type': self.element((By.ID, f'evaluation-{idx}-evaluationType')).text.strip(),
                    'dates': self.element((By.ID, f'evaluation-{idx}-period')).text.split('\n')[0],
                },
            )
        return data

    def eval_row_el(self, evaluation):
        return self.element((By.XPATH, self.eval_row_xpath(evaluation)))

    def eval_status_el(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "status")]'
        return self.element((By.XPATH, xpath))

    def eval_status(self, evaluation):
        return self.eval_status_el(evaluation).text

    def eval_last_update(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "lastUpdated")]'
        return self.element((By.XPATH, xpath)).text

    def eval_ccn(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "courseNumber")]'
        return self.element((By.XPATH, xpath)).text.strip().split('\n')[0]

    def eval_course(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}//div[contains(@id, "courseName")]'
        return self.element((By.XPATH, xpath)).text

    def eval_course_title(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}//div[contains(@id, "courseTitle")]'
        return self.element((By.XPATH, xpath)).text

    def eval_instructor(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "instructor")]'
        return self.element((By.XPATH, xpath)).text

    def eval_dept_form(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "departmentForm")]'
        return self.element((By.XPATH, xpath)).text.strip()

    def eval_type(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "evaluationType")]'
        return self.element((By.XPATH, xpath)).text.strip()

    def eval_period_dates(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "period")]'
        return self.element((By.XPATH, xpath)).text.strip()

    def eval_period_duration(self, evaluation):
        xpath = f'{self.eval_row_xpath(evaluation)}/td[contains(@id, "period")]/span/div[2]'
        return self.element((By.XPATH, xpath)).text.strip()

    # FILTERING

    SEARCH_INPUT = (By.ID, 'evaluation-search-input')

    def filter_rows(self, search_string):
        app.logger.info(f'Filtering table by {search_string}')
        self.remove_and_enter_chars(CourseDashboards.SEARCH_INPUT, search_string)
        time.sleep(2)

    # SORTING

    def sort_asc(self, header_string):
        self.wait_for_element((By.XPATH, f'//th[contains(., "{header_string}")]'), utils.get_short_timeout())
        el = self.element((By.XPATH, f'//th[contains(., "{header_string}")]'))
        sort = el.get_attribute('aria-sort')
        if sort == 'none' or sort == 'descending':
            el.click()
            if sort == 'descending':
                time.sleep(utils.get_click_sleep())
                el.click()
        time.sleep(2)

    def sort_desc(self, header_string):
        self.wait_for_element((By.XPATH, f'//th[contains(., "{header_string}")]'), utils.get_short_timeout())
        el = self.element((By.XPATH, f'//th[contains(., "{header_string}")]'))
        sort = el.get_attribute('aria-sort')
        if sort == 'none' or sort == 'ascending':
            el.click()
            if sort == 'none':
                time.sleep(utils.get_click_sleep())
                el.click()
        time.sleep(2)

    @staticmethod
    def sort_default(evaluations, reverse=False):
        evaluations.sort(
            key=lambda e: (
                e.subject,
                int(''.join([i for i in e.catalog_id if i.isdigit()])),
                (e.catalog_id.split(''.join([i for i in e.catalog_id if i.isdigit()]))[1]),
                e.instruction_format,
                e.section_num,
                (e.eval_type or ''),
                (e.dept_form or ''),
                (e.instructor.last_name.lower() if e.instructor.uid else ''),
                (e.instructor.first_name.lower() if e.instructor.uid else ''),
                e.eval_start_date,
            ),
            reverse=reverse,
        )

    @staticmethod
    def split_listings(dept, evaluations):
        dept_subj = utils.get_dept_subject_areas(dept)
        dept_listings = list(filter(lambda e: e.subject in dept_subj, evaluations))
        foreign_listings = [e for e in evaluations if e not in dept_listings]
        foreign_listings.sort(
            key=lambda e: (
                e.subject,
                (e.instructor.last_name.lower() if e.instructor.uid else ''),
                (e.instructor.first_name.lower() if e.instructor.uid else ''),
            ),
        )
        return dept_listings, foreign_listings

    @staticmethod
    def insert_listings(evaluations, listings, reverse=False):
        all_evaluations = []
        key = lambda c: c.ccn
        grouped_evals = itertools.groupby(evaluations, key)
        for k, g in grouped_evals:
            grp = list(g)
            if not reverse:
                for i in grp:
                    all_evaluations.append(i)
            matches = []
            for x in listings:
                if grp[0].x_listing_ccns:
                    if x.ccn in grp[0].x_listing_ccns:
                        matches.append(x)
                elif grp[0].room_share_ccns:
                    if x.ccn in grp[0].room_share_ccns:
                        matches.append(x)
            for m in matches:
                all_evaluations.append(m)
            if reverse:
                for i in grp:
                    all_evaluations.append(i)
        return all_evaluations

    @staticmethod
    def get_catalog_id_suffix(evaluation):
        num = ''.join([i for i in evaluation.catalog_id if i.isdigit()])
        return evaluation.catalog_id.split(num)[1]

    def sort_by_course(self, dept, evaluations, reverse=False):
        split_listings = self.split_listings(dept, evaluations)
        split_listings[0].sort(
            key=lambda e: (
                e.subject,
                int(''.join([i for i in e.catalog_id if i.isdigit()])),
                (e.catalog_id.split(''.join([i for i in e.catalog_id if i.isdigit()]))[1]),
                e.instruction_format,
                e.section_num,
                (e.eval_type or ''),
                (e.dept_form or ''),
                (e.instructor.last_name.lower() if e.instructor.uid else ''),
                (e.instructor.first_name.lower() if e.instructor.uid else ''),
                e.eval_start_date,
            ),
            reverse=reverse,
        )
        return self.insert_listings(split_listings[0], split_listings[1], reverse)

    def sort_by_status(self, dept, evaluations, reverse=False):
        evaluations = self.sort_by_course(dept, evaluations)
        evaluations.sort(
            key=lambda e: (e.status.value['ui'] if e.status else ''),
            reverse=reverse,
        )
        return evaluations

    def sort_by_ccn(self, dept, evaluations, reverse=False):
        dept_subj = utils.get_dept_subject_areas(dept)
        dept_listings = list(filter(lambda e: e.subject in dept_subj, evaluations))
        foreign_listings = [e for e in evaluations if e not in dept_listings]
        dept_listings.sort(
            key=lambda e: (
                int(e.ccn),
                (e.eval_type or ''),
                (e.dept_form or ''),
                (e.instructor.last_name.lower() if e.instructor.uid else ''),
                (e.instructor.first_name.lower() if e.instructor.uid else ''),
                e.eval_start_date,
            ),
            reverse=reverse,
        )
        return self.insert_listings(dept_listings, foreign_listings, reverse)

    def sort_by_instructor(self, dept, evaluations, reverse=False):
        evaluations = self.sort_by_course(dept, evaluations)
        evaluations.sort(
            key=lambda e: (
                (e.instructor.last_name.lower() if e.instructor.uid else ''),
                (e.instructor.first_name.lower() if e.instructor.uid else ''),
            ),
            reverse=reverse,
        )
        return evaluations

    def sort_by_dept_form(self, dept, evaluations, reverse=False):
        evaluations = self.sort_by_course(dept, evaluations)
        evaluations.sort(
            key=lambda e: (
                (e.dept_form or ''),
            ),
            reverse=reverse,
        )
        return evaluations

    def sort_by_eval_type(self, dept, evaluations, reverse=False):
        evaluations = self.sort_by_course(dept, evaluations)
        evaluations.sort(
            key=lambda e: (
                (e.eval_type or ''),
            ),
            reverse=reverse,
        )
        return evaluations

    def sort_by_eval_period(self, dept, evaluations, reverse=False):
        evaluations = self.sort_by_course(dept, evaluations)
        evaluations.sort(
            key=lambda e: (
                e.eval_start_date,
            ),
            reverse=reverse,
        )
        return evaluations

    @staticmethod
    def sorted_eval_data(evaluations):
        data = []
        for e in evaluations:
            data.append(
                {
                    'ccn': e.ccn,
                    'listings': (e.x_listing_ccns or e.room_share_ccns),
                    'course': f'{e.subject} {e.catalog_id} {e.instruction_format} {e.section_num}',
                    'uid': (e.instructor.uid or ''),
                    'form': (e.dept_form or ''),
                    'type': (e.eval_type or ''),
                },
            )
        unique = []
        [unique.append(i) for i in data if i not in unique]
        return unique

    def visible_sorted_eval_data(self):
        data = self.visible_eval_data()
        for d in data:
            d.pop('dates')
            d.pop('name')
        return data
