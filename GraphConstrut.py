import pandas as pd
import ast
from haversine import haversine, Unit
import igraph
import folium

path = '../数据/WithVirtualNode.csv'

df = pd.read_csv(path, encoding='gbk')
vertex_attrs = {"Name": df['EN_NAME'].values,
                "Center": df['Center'].values,
                "True": df['TRUE'].values}##点特性
def Distance(start:int, dest:int)->float:
    lati1, longti1 = vertex_attrs['Center'][start].strip('()[]').split(',')
    lati2, longti2 = vertex_attrs['Center'][dest].strip('()[]').split(',')
    coord1 = (float(lati1), float(longti1))
    coord2 = (float(lati2), float(longti2))
    distance = haversine(coord1, coord2, unit=Unit.KILOMETERS)
    return distance


edges = []
lenth = []
for idx,row in df.iterrows():
    NeighborList = ast.literal_eval(row['Neighbor1'])
    for neighbor in NeighborList:
        sorted_tuple = tuple(sorted(tuple((idx, neighbor))))
        if sorted_tuple not in edges:
            edges.append(sorted_tuple)
            lenth.append(Distance(idx, neighbor))
edge_attrs = {'lenth': lenth}
MyGraph = igraph.Graph(n = len(vertex_attrs['Name']), \
                       edges=edges, directed = False, \
                        vertex_attrs = vertex_attrs, \
                        edge_attrs = edge_attrs)

if __name__ == '__main__':
    m = folium.Map(zoom_start=6, location=(40,116))

    for i in range(len(vertex_attrs['Center'])):
        name = vertex_attrs['Name'][i]
        Center = ast.literal_eval(vertex_attrs['Center'][i])
        folium.CircleMarker(
            location=Center,
            radius=8,
            fill=True,
            color='blue'
        ).add_to(m)
        folium.Marker(
            location=Center,
            icon=folium.DivIcon(html=f'<div>{name}</div>')
        ).add_to(m)

    for edge in MyGraph.get_edgelist():
        start, end = edge[0], edge[1]
        folium.PolyLine([ast.literal_eval(vertex_attrs['Center'][start]), ast.literal_eval(vertex_attrs['Center'][end])],\
                        color = 'red').add_to(m)
    # m.save('graph_on_map_withVirtual.html')