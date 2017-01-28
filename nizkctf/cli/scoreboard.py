# -*- encoding: utf-8 -*-

from __future__ import unicode_literals, division, print_function,\
                       absolute_import
import sys
import json
import operator
import tempfile
import subprocess
import codecs
from ..text import width
from ..six import viewitems


def rank():
    '''
    Compute ranking given a submissions file.

    Args:
        f (file): File-like object with the submissions json.

    Returns:
        List containing the computed ranking for the submission list.
        The result is in the following format:

        (team, score)

        And a map containing submissions sorted by team.
    '''

    from ..acceptedsubmissions import AcceptedSubmissions

    submissions = {}
    scores = {}
    for subm in AcceptedSubmissions:
        team = subm['team']
        scores[team] = scores.get(team, 0) + subm['points']
        submissions.setdefault(team, []).append(subm)

    return (sorted(viewitems(scores), key=operator.itemgetter(1),
            reverse=True), submissions)


def pprint(ranking, top=0):
    '''
    Pretty print scoreboard in terminal.

    Args:
        ranking (list): List of tuples containing teams and scores.
        top (int): Number of teams to show in scoreboard.

    '''

    if top == 0:
        top = len(ranking)

    team_len = max(width(team) for team, score in ranking[:top])
    team_len = max(team_len, 10)

    pos_len = score_len = 6

    def hyph(n):
        return '-'*(n + 2)

    sep = hyph(pos_len) + '+' + hyph(team_len) + '+' + hyph(score_len)

    def fmtcol(s, n):
        return ' ' + s + ' '*(n - width(s) + 1)

    def fmt(pos, team, score):
        return fmtcol(pos, pos_len) + '|' + \
               fmtcol(team, team_len) + '|' + \
               fmtcol(score, score_len)

    print('')
    print(sep)
    print(fmt('Pos', 'Team', 'Score'))
    print(sep)

    for idx, (team, score) in enumerate(ranking[0:top]):
        pos = '%d' % (idx + 1)
        print(fmt(pos, team, '%d' % score))

    print(sep)
    print('')


def plot(ranking, submissions, top=3):
    '''
    Plot points for top teams.

    Args:
        ranking (list): List containing teams and scores sorted in
            descending order.
        submissions (dict): Dict [team] -> submission list.
        top (int): Number of teams to appear in chart.
    '''

    from ..acceptedsubmissions import TIME_FORMAT

    # generate temporary files with data points
    fnames = []
    for team, _ in ranking[0:top]:
        f = tempfile.NamedTemporaryFile(suffix='.dat',
                                        prefix='nizkctf-', delete=True)
        w = codecs.getwriter('utf-8')(f)
        partial = 0
        for subm in submissions[team]:
            partial += subm['points']
            w.write('%s, %d\n' % (subm['time'], partial))
        w.flush()
        fnames.append((team, f))

    # generate gnuplot file
    f = tempfile.NamedTemporaryFile(suffix='.gp',
                                    prefix='nizkctf-', delete=True)
    w = codecs.getwriter('utf-8')(f)
    w.write('set terminal dumb 120 30\n')
    w.write('set xdata time\n')
    w.write('set datafile sep \',\'\n')
    w.write('set timefmt "%s"\n' % TIME_FORMAT)
    w.write('set style data steps\n')
    w.write('plot ')
    fmt = '\'%s\' using 1:2 title \'%s\''
    w.write(fmt % (fnames[0][1].name, fnames[0][0]))
    for team, ft in fnames[1:]:
        w.write(', ')
        w.write(fmt % (ft.name, team))
    w.flush()

    # plot in terminal
    p = subprocess.Popen(['gnuplot', f.name],
                         stderr=sys.stderr,
                         stdout=sys.stdout)
    p.wait()

    # close/delete files
    f.close()
    for nm, f in fnames:
        f.close()
