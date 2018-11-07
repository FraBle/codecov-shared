from covreports.utils.tuples import ReportTotals
from covreports.helpers.numeric import ratio

from operator import itemgetter


def agg_totals(totals):
    totals = [_f for _f in totals if _f]
    n_files = len(totals)
    totals = list(map(_sum, zip(*totals)))
    if not totals:
        return list(ReportTotals.__new__.__defaults__)
    totals[0] = n_files
    totals[5] = ratio(totals[2], totals[1])
    return totals


def sum_totals(totals):
    totals = [_f for _f in totals if _f]
    if not totals:
        return ReportTotals()

    sessions = totals[0][9]
    lines = sum(map(itemgetter(1), totals))
    hits = sum(map(itemgetter(2), totals))
    return ReportTotals(files=len(totals),
                        lines=lines,
                        hits=hits,
                        misses=sum(map(itemgetter(3), totals)),
                        partials=sum(map(itemgetter(4), totals)),
                        branches=sum(map(itemgetter(6), totals)),
                        methods=sum(map(itemgetter(7), totals)),
                        messages=sum(map(itemgetter(8), totals)),
                        coverage=ratio(hits, lines),
                        sessions=sessions,
                        complexity=sum(map(itemgetter(10), totals)),
                        complexity_total=sum(map(itemgetter(11), totals)))

def _sum(array):
    if array:
        if not isinstance(array[0], (type(None), str)):
            try:
                return sum(array)
            except:
                # https://sentry.io/codecov/v4/issues/159966549/
                return sum([a if type(a) is int else 0 for a in array])
    return None

