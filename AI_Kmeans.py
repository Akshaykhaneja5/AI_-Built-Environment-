import Rhino.Geometry as rg
import random
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import rhinoscriptsyntax as rs
import scriptcontext as sc
import math

geometry = geometry  
num_points = int(Pt_Count)  
num_clusters = int(Cl_Count)  
if not isinstance(geometry, rg.Brep):
    try:
        # Try to convert to Brep
        if isinstance(geometry, rg.Extrusion):
            geometry = geometry.ToBrep()
        elif isinstance(geometry, rg.Mesh):
            geometry = rg.Brep.CreateFromMesh(geometry, True)
        else:
            geometry = rg.Brep.TryConvertBrep(geometry)
    except Exception as e:
        
        print("Conversion error:", e)

bbox = geometry.GetBoundingBox(True)
min_point = bbox.Min
max_point = bbox.Max


candidate_points = []
points_inside = []


for _ in range(num_points * 5):  
    x = random.uniform(min_point.X, max_point.X)
    y = random.uniform(min_point.Y, max_point.Y)
    z = random.uniform(min_point.Z, max_point.Z)
    candidate_points.append(rg.Point3d(x, y, z))


for point in candidate_points:
    
    if rg.Brep.IsPointInside(geometry, point, 0.01, True):
        points_inside.append(point)
        if len(points_inside) >= num_points:
            break


if len(points_inside) < num_points:
    remaining = num_points - len(points_inside)
    for _ in range(remaining):
        x = random.uniform(min_point.X, max_point.X)
        y = random.uniform(min_point.Y, max_point.Y)
        z = random.uniform(min_point.Z, max_point.Z)
        temp_point = rg.Point3d(x, y, z)
        
        success, t, closest_point = geometry.ClosestPoint(temp_point)
        if success:
            points_inside.append(closest_point)
        else:
            
            points_inside.append(temp_point)


if len(points_inside) < 2:
    raise Exception("Not enough points found inside or on the geometry")


data = np.array([[p.X, p.Y, p.Z] for p in points_inside])


actual_clusters = min(num_clusters, len(points_inside))
kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
labels = kmeans.fit_predict(data)
centroid_points = [rg.Point3d(c[0], c[1], c[2]) for c in kmeans.cluster_centers_]

silhouette = None
if actual_clusters > 1 and len(points_inside) > actual_clusters:
    try:
        silhouette = silhouette_score(data, labels)
    except:
        silhouette = None


clusters = {}
for i, label in enumerate(labels):
    if label not in clusters:
        clusters[label] = []
    clusters[label].append(points_inside[i])


boxes = []
for cluster_id, cluster_points in clusters.items():
    if len(cluster_points) > 0:
       
        cluster_bbox = rg.BoundingBox(cluster_points)
        if cluster_bbox.IsValid:
           
            box = rg.Box(cluster_bbox)
            boxes.append(box.ToBrep())


result_geometry = geometry
for box in boxes:
    try:
        
        diff_result = rg.Brep.CreateBooleanDifference([result_geometry], [box], 0.01)
        if diff_result and len(diff_result) > 0:
            result_geometry = diff_result[0]
    except Exception as e:
        
        print(f"Boolean operation failed: {e}")


flat_points = points_inside
cluster_indices = labels.tolist()  


if actual_clusters > 1:
    normalized_indices = [i / (actual_clusters - 1) for i in cluster_indices]
else:
    normalized_indices = [0] * len(cluster_indices)


a = flat_points          
b = centroid_points      
c = silhouette           
d = normalized_indices   
e = boxes                
f = result_geometry      