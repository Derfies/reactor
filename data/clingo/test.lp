node(1..3).
type(foyer).
type(toilet).
type(cinema).

num(foyer, 1).
num(toilet, 1).
num(cinema, 1).


3 { node_type(N, T) : type(T) } 3 :- node(N).


#count{ node }.


%#show node_type/2.



% Assign node type to each node.
1 { node_type(N, T) : type(T) } 1 :- node(N).




#show node_type/2.



% Count the number of types.
type_num(T, Num) :- Num = #count{ N : node_type(N, T)}, type(T).

% Remove any type which is greater than 1.
:- node_type(N, T), type_num(T, Num), Num > 1.