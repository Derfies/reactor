% do connectivity
% weights?
% at least n nodes apart, distance range?

#const num_nodes=0.

% Make inverse edges facts to make the graph undirected.
edge(X, Y) :- edge(Y, X).

% Make inverse adjacencies.
adjacency(X, Y) :- adjacency(Y, X).

type(T) :- type_range(T, _, _).

1 { node_type(N, T) : type(T) } 1 :- node(N).

% Remove those that don't fulfil the min / max required types.
type_num(T, Num) :- Num = #count{ N : node_type(N, T)}, type(T).
:- type_num(Type, Num), type_range(Type, Min, Max), Num > Max.
:- type_num(Type, Num), type_range(Type, Min, Max), Num < Min.

% Remove those that don't follow constraint rules.
:- edge(Head, Tail), node_type(Head, HeadType), node_type(Tail, TailType), not adjacency(HeadType, TailType).

#show node_type/2.
#show type_num/2.
#show adjacency/2.
#show foo/2.
#show bar/2.