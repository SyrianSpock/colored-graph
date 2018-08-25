import argparse
from collections import defaultdict, namedtuple
from functools import reduce
import time
import os

from graphviz import Digraph
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


Edge = namedtuple('Edge', ['src', 'dst', 'color'])
Node = namedtuple('Node', ['name', 'color', 'rank'])
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

        subgraphs = split_subgraphs(lines)

        return parse_header(header), subgraphs

def split_subgraphs(lines):
    def _slice(lines, separator):
        for i, elem in enumerate(lines[1:]):
            if not elem.startswith(separator):
                return [lines[:i+1]] + _slice(lines[i+1:], separator)
        return [lines]

    subgraphs = _slice(lines, ' ')[:-1]
    subgraphs = list(map(parse_single_graph, subgraphs))
    return subgraphs

def remove_duplicates(nodes):
    def find_duplicate(node, nodes):
        return any(node for node in node_already_added(nodes))

    def remove_node_by_name(node, nodes):
        match = next(x for x in filtered_nodes if x.name == node.name)
        filtered_nodes.remove(match)
        return filtered_nodes, match

    filtered_nodes = []
    for node in nodes:
        node_already_added = lambda nodes: filter(lambda x: x.name == node.name, nodes)
        if find_duplicate(node, filtered_nodes):
            filtered_nodes, match = remove_node_by_name(node, filtered_nodes)
            match = Node(name=match.name, color=match.color, rank=min(match.rank, node.rank))
            filtered_nodes.append(match)
        else:
            filtered_nodes.append(node)

    return filtered_nodes

def parse_single_graph(lines):
    lines = list(filter(lambda line: all(symbol not in line.lstrip() for symbol in COMMENT_SYMBOLS), lines))
    lines = list(map(replace_bad_characters, lines))
    lines = list(map(lambda line: line.replace('\t', ' ' * 4), lines))
    tasks = list((line.lstrip(), _depth_level(line)) for line in lines if len(line) > 0)

    root, tasks = tasks[0], tasks[1:]

    root = Node(name=_task_strip(root[0]), color=_task_color(root[0]), rank=0)
    nodes = list(Node(name=_task_strip(task), color=_task_color(task), rank=depth) for task, depth in set(tasks))
    edges = list(Edge(src=_task_strip(src), dst=_task_strip(dst), color=_task_color(src))
                     for src, dst in set(_node_pairs(tasks, list(), list())))

    nodes = remove_duplicates(nodes)

    return root, nodes, edges

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

def draw_graph(colors, subgraphs, format):
    graph = Digraph(strict=True, format=format, node_attr={'shape': 'box'})

    for subgraph in subgraphs:
        root, nodes, edges = subgraph

        cluster = Digraph(name='cluster_' + root.name, graph_attr={'label': root.name, 'color': _sanitize_color(root.color, colors)})

        for node in nodes: _append_node(cluster, node, color_palette=colors)
        for edge in edges: _append_edge(cluster, edge, color_palette=colors)
        cluster = constrain_nodes_on_same_level(cluster, nodes)

        graph.subgraph(cluster)

    return graph

def constrain_nodes_on_same_level(graph, nodes):
    ranks = []
    for node in nodes:
        while node.rank > len(ranks):
            ranks.append([])
        ranks[node.rank - 1].append(str(node.name))

    for rank in ranks:
        all_nodes = '; '.join(list(map(lambda x: '"' + x + '"', rank)))
        graph.body.append('\t{rank = same; ' + all_nodes + '}')

    return graph

def _sanitize_color(color, color_palette):
    return color_palette[color] if color in color_palette.keys() else color

def _append_node(graph, node, color_palette):
    color = _sanitize_color(node.color, color_palette)
    graph.node(node.name, color=color, fontcolor=color, group=str(node.rank))

def _append_edge(graph, edge, color_palette):
    color = _sanitize_color(edge.color, color_palette)
    graph.edge(edge.src, edge.dst, color=color)

def render_graph(description, view, output_file, format):
    header, subgraphs = parse_description(description)
    graph = draw_graph(header, subgraphs, format=format)

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
