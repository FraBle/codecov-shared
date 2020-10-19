use crate::cov;

use pyo3::prelude::*;

use std::collections::HashMap;

pub enum CoverageType {
    Standard,
    Branch,
    Method,
}

pub struct LineSession {
    pub id: i32,
    pub coverage: cov::Coverage,
    pub branches: i32,
    pub partials: Vec<i32>,
    pub complexity: i32,
}

pub struct ReportLine {
    pub coverage: cov::Coverage,
    pub coverage_type: CoverageType,
    pub sessions: Vec<LineSession>,
    pub complexity: Option<i32>, // This has to be redone
}

impl ReportLine {
    fn calculate_sessions_coverage(&self, session_ids: &Vec<i32>) -> cov::Coverage {
        let valid_sessions: Vec<&cov::Coverage> = self
            .sessions
            .iter()
            .filter(|k| session_ids.contains(&k.id))
            .map(|k| &k.coverage)
            .collect();
        return cov::Coverage::join_coverages(valid_sessions);
    }
}

pub struct ReportFile {
    pub lines: HashMap<i32, ReportLine>,
}

#[pyclass]
pub struct Report {
    pub filenames: HashMap<String, i32>,
    pub report_files: Vec<ReportFile>,
    pub session_mapping: HashMap<i32, Vec<String>>,
}

impl ReportFile {
    pub fn get_eof(&self) -> i32 {
        return match self.lines.keys().max() {
            Some(expr) => *expr,
            None => 0,
        };
    }

    fn get_filtered_totals(&self, sessions: &Vec<i32>) -> cov::ReportTotals {
        let mut res = cov::ReportTotals {
            files: 1,
            lines: 0,
            hits: 0,
            misses: 0,
            partials: 0,
            branches: 0,
            sessions: 0,
            complexity: 0,
            complexity_total: 0,
        };
        for (_, line) in self.lines.iter() {
            res.lines += 1;
            match line.calculate_sessions_coverage(sessions) {
                cov::Coverage::Hit => {
                    res.hits += 1;
                }
                cov::Coverage::Miss => {
                    res.misses += 1;
                }
                cov::Coverage::Partial(_) => {
                    res.partials += 1;
                }
            }
        }
        return res;
    }

    fn calculate_per_flag_totals(
        &self,
        flag_mapping: &HashMap<i32, Vec<String>>,
    ) -> HashMap<String, cov::ReportTotals> {
        let mut book_reviews: HashMap<String, cov::ReportTotals> = HashMap::new();
        for (_, report_line) in self.lines.iter() {
            for sess in &report_line.sessions {
                match flag_mapping.get(&sess.id) {
                    Some(flags) => {
                        for f in flags {
                            let mut stat =
                                book_reviews
                                    .entry(f.to_string())
                                    .or_insert(cov::ReportTotals {
                                        files: 1,
                                        lines: 0,
                                        hits: 0,
                                        misses: 0,
                                        partials: 0,
                                        branches: 0,
                                        sessions: 0,
                                        complexity: 0,
                                        complexity_total: 0,
                                    });
                            stat.lines += 1;
                            match sess.coverage {
                                cov::Coverage::Hit => stat.hits += 1,
                                cov::Coverage::Miss => stat.misses += 1,
                                cov::Coverage::Partial(_) => stat.partials += 1,
                            }
                        }
                    }
                    None => {}
                }
            }
        }
        return book_reviews;
    }

    fn get_totals(&self) -> cov::ReportTotals {
        let mut res: cov::ReportTotals = cov::ReportTotals {
            files: 1,
            lines: 0,
            hits: 0,
            misses: 0,
            partials: 0,
            branches: 0,
            sessions: 0,
            complexity: 0,
            complexity_total: 0,
        };
        for (_, report_line) in self.lines.iter() {
            res.lines += 1;
            match report_line.coverage {
                cov::Coverage::Hit => res.hits += 1,
                cov::Coverage::Miss => res.misses += 1,
                cov::Coverage::Partial(_) => res.partials += 1,
            }
        }
        return res;
    }
}

impl Report {
    fn get_sessions_from_flags(&self, flags: &Vec<&str>) -> Vec<i32> {
        let mut res: Vec<i32> = Vec::new();
        for (session_id, session_flags) in self.session_mapping.iter() {
            if flags.iter().any(|v| session_flags.contains(&v.to_string())) {
                res.push(*session_id); // TODO Do I have to use this * ?
            }
        }
        return res;
    }
}

#[pymethods]
impl Report {
    fn get_filtered_totals(&self, files: Vec<&str>, flags: Vec<&str>) -> cov::ReportTotals {
        let sessions = self.get_sessions_from_flags(&flags);
        let mut initial = cov::ReportTotals {
            files: 0,
            lines: 0,
            hits: 0,
            misses: 0,
            partials: 0,
            branches: 0,
            sessions: 0,
            complexity: 0,
            complexity_total: 0,
        };
        for filename in files {
            let location = self.filenames.get(filename);
            if let Some(i) = location {
                let report_file = &self.report_files[*i as usize];
                let some_totals = report_file.get_filtered_totals(&sessions);
                initial.add_up(&some_totals);
            }
        }
        return initial;
    }

    pub fn calculate_per_flag_totals(&self) -> HashMap<String, cov::ReportTotals> {
        let mut book_reviews: HashMap<String, cov::ReportTotals> = HashMap::new();
        for report_file in self.report_files.iter() {
            let file_totals = report_file.calculate_per_flag_totals(&self.session_mapping);
            for (flag_name, totals) in file_totals.iter() {
                let mut current =
                    book_reviews
                        .entry(flag_name.to_string())
                        .or_insert(cov::ReportTotals {
                            files: 0,
                            lines: 0,
                            hits: 0,
                            misses: 0,
                            partials: 0,
                            branches: 0,
                            sessions: 0,
                            complexity: 0,
                            complexity_total: 0,
                        });
                current.files += totals.files;
                current.lines += totals.lines;
                current.hits += totals.hits;
                current.misses += totals.misses;
                current.partials += totals.partials;
                current.branches += totals.branches;
                current.sessions += totals.sessions;
                current.complexity += totals.complexity;
                current.complexity_total += totals.complexity_total;
            }
        }
        return book_reviews;
    }

    pub fn get_totals(&self) -> PyResult<cov::ReportTotals> {
        let mut res: cov::ReportTotals = cov::ReportTotals {
            files: 0,
            lines: 0,
            hits: 0,
            misses: 0,
            partials: 0,
            branches: 0,
            sessions: 0,
            complexity: 0,
            complexity_total: 0,
        };
        for report_file in self.report_files.iter() {
            let totals = report_file.get_totals();
            res.files += totals.files;
            res.lines += totals.lines;
            res.hits += totals.hits;
            res.misses += totals.misses;
            res.partials += totals.partials;
            res.branches += totals.branches;
            res.sessions += totals.sessions;
            res.complexity += totals.complexity;
            res.complexity_total += totals.complexity_total;
        }
        return Ok(res);
    }
}

#[pymethods]
impl Report {
    pub fn get_eof(&self, file_number: i32) -> i32 {
        let file = &self.report_files[file_number as usize];
        file.get_eof()
    }
}
