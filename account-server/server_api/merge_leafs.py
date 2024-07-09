
def merge_leafs(data, update):
    """ Asigna a data las keys que estan en update y no en data. Si hay keys que estan en update y en data entonces
    se asigna, a data, el value de update si, y solo si, ambos values no son dicts.
    Esta funcion solo permite actualizar values que NO son dicts en data.
    Tambien permite insertar nuevas keys en data asignandoles cualquier value. Esto sucede cuando la key de update
    no existe en data.
    La estructura de datos en data puede ser considerada un arbol donde las ramas estan compuestas por values que son dicts
    y las hojas con values que no son dicts.
    Leafs (hojas) son considerados todos los values que no son dict en data. Eso es lo que se permite actualizar en data.
    Esta funcion permite insertar una rama en data a condicion de que la key de la raiz (value sera un dict) de dicha rama
    no exista en data.
    ATENCION: update no debe ser modificado despues de llamar a esta funcion pues puede tener objetos compartidos
    con data y se modificaran. """
    assert isinstance(data, dict)
    assert isinstance(update, dict)

    nodes = [(data, update)]

    while len(nodes) != 0:
        ra, rb = nodes.pop(0)
    
        for x in rb.keys():
            if x in ra.keys():
                if isinstance(rb[x], dict) and isinstance(ra[x], dict):
                    # Los dos son dict asi que la pareja se añade a la lista de nodos para seguir buscando.
                    nodes.append((ra[x], rb[x]))
                elif not isinstance(rb[x], dict) and not isinstance(ra[x], dict):
                    # UPDATE
                    ra[x] = rb[x]
                elif isinstance(rb[x], dict) and not isinstance(ra[x], dict):
                    # Error: Se intenta asignar un dict a algo que NO es un dict en data.
                    assert False
                elif not isinstance(rb[x], dict) and isinstance(ra[x], dict):
                    # Error: Se intenta asignar algo que no es un dict a algo que es un dict en data.
                    assert False
            else:
                ra[x] = rb[x]

if __name__ == "__main__":

    A = {'key1': {'b':23}, 'key2': { 'key21': [1,2], 'key22': 2 }}
    B = {'key1': {'a':3}, 'key3': {}}
    merge_leafs(A, B)

    print(A)




