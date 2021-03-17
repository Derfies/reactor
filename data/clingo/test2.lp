

type_range(foyer, 1, 1).
type_range(toilet, 1, 1).
type_range(cinema, 1, 1).
type_range(hallway, 0, 10).

type(T) :- type_range(T, _, _).

1 { node_type(N, T) : type(T) } 1 :- node(N).

type_num(T, Num) :- Num = #count{ N : node_type(N, T)}, type(T).

%:- node_type(Node, Type), type_num(Type, Num), type_range(Type, Min, Max), Min < Num, Num < Max.
%:- node_type(N, T), type_num(T, Num), Num > 1.

:- node_type(Node, Type), type_num(Type, Num), type_range(Type, Min, Max), Num < Min.
:- node_type(Node, Type), type_num(Type, Num), type_range(Type, Min, Max), Num > Max.


#show node_type/2.