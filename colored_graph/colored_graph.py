import argparse
from collections import defaultdict, namedtuple
import time
import os

from graphviz import Digraph
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


Edge = namedtuple('Edge', ['src', 'dst', 'color'])
Node = namedtuple('Node', ['name', 'color'])
COMMENT_SYMBOLS = ['#', '//']

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate colored graph from description.')

    parser.add_argument('file', type=str, help='Graph description file')
    parser.add_argument('-o', '--output', type=str, help='Graph output file base name (no extension)')
    parser.add_argument('-f', '--format', type=str, default='pdf', help='Graph output format (default: pdf)')
    parser.add_argument('-v', '--view', action='store_true', help='View generated graph')
    parser.add_argument('-w', '--watch', action='store_true',
                        help='Watch graph description file for changes and regenerate graph')

    return parser.parse_args()

def replace_bad_characters(line):
    return line \
        .replace(':', 'ː') \
        .replace('(', '\\(') \
        .replace(')', '\\)') \

def parse_description(description_file):
    with open(description_file, 'r') as file:
        text = file.read()
        lines = text.split('\n')

        header = lines[0] if _is_valid_header(lines[0]) else None
        lines = lines[1:] if header else lines

        lines = list(filter(lambda line: all(symbol not in line.lstrip() for symbol in COMMENT_SYMBOLS), lines))
        lines = list(map(replace_bad_characters, lines))
        lines = list(map(lambda line: line.replace('\t', ' ' * 4), lines))
        tasks = list((line.lstrip(), _depth_level(line)) for line in lines if len(line) > 0)

        nodes = list(Node(name=_task_strip(task), color=_task_color(task)) for task, depth in set(tasks))
        edges = list(Edge(src=_task_strip(src), dst=_task_strip(dst), color=_task_color(src))
                         for src, dst in set(_node_pairs(tasks, list(), list())))

        return parse_header(header), nodes, edges

def parse_header(header):
    if header is None: return {}
    fields = header[1:-1].split(',')
    split = lambda x: x.split(':')
    strip = lambda x: x.lstrip()
    pairs = list(map(split, (map(strip, fields))))
    colors = dict(pairs)
    return colors

def _is_valid_header(line):
    return line.startswith('[') and line.endswith(']')

def _task_color(task):
    return task.split(' ')[0]

def _task_strip(task):
    return ' '.join(task.split(' ')[1:]).lstrip()

def _depth_level(line):
    return int(_count_indentation(line) / 4)

def _count_indentation(line, count=0):
    if line.startswith(' '): return _count_indentation(line[1:], count + 1)
    else:                    return count

def _node_pairs(tasks, pairs, parents):
    if len(tasks) == 0: return pairs

    child, depth = tasks[0]

    if len(parents):
        for parent, parent_depth in reversed(parents):
            if parent_depth < depth:
                pairs.append((parent, child))
                break

    if len(parents) != depth:
        return _node_pairs(tasks=tasks[1:], pairs=pairs, parents=[*parents[:depth], (child, depth)])
    else:
        return _node_pairs(tasks=tasks[1:], pairs=pairs, parents=[*parents, (child, depth)])

def draw_graph(colors, nodes, edges, format):
    graph = Digraph(strict=True, format=format)
    for node in nodes: _append_node(graph, node, color_palette=colors)
    for edge in edges: _append_edge(graph, edge, color_palette=colors)
    return graph

def _append_node(graph, node, color_palette):
    color = node.color
    if color in color_palette.keys(): color = color_palette[color]
    graph.node(node.name, color=color, fontcolor=color)

def _append_edge(graph, edge, color_palette):
    color = edge.color
    if color in color_palette.keys(): color = color_palette[color]
    graph.edge(edge.src, edge.dst, color=color)

def render_graph(description, view, output_file, format):
    graph = draw_graph(*parse_description(description), format=format)

    output_dir = os.path.dirname(output_file or '')
    output_gv = os.path.join(output_dir, os.path.basename(output_file or 'graph') + '.gv')
    graph.render(filename=output_gv, view=view, cleanup=True)

    if output_file:
        graph.save(output_file)

def main():
    args = parse_arguments()

    render_graph(args.file, args.view, args.output, args.format)

    if args.watch:
        class GraphWatcher(FileSystemEventHandler):
            def on_modified(self, event):
                if event == FileModifiedEvent(os.path.join('.', args.file)):
                    render_graph(args.file, args.view, args.output, args.format)

        event_handler = GraphWatcher()
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(args.file) or '.', recursive=False)
        observer.start()

        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()

if __name__ == '__main__':
    main()
