import re

def sub_latex(line):
    latex = re.search(r'(.*?)\\\[ (.+?) \\\](.*?)', line)
    if latex != None:
        start = re.search(r'.?\\\[', latex.group(0))
        start = start.group(0)
        if len(start) < 3 or start[0] != '\\':
            before = latex.group(1)
            after = latex.group(3)
            latex = latex.group(2)

            latex_start = '[latex]\\begin{math}'
            latex_end = '\\end{math}[\\latex]'

            line = before + latex_start + latex + latex_end + after
        else:
            line = re.sub(r'\\\\\[', '\[', line)
            line = re.sub(r'\\\\\]', '\]', line)
    return line