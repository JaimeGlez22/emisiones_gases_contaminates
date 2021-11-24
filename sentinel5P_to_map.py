
from netCDF4 import Dataset
import numpy as np
import os
import conda

conda_file_dir = conda.__file__
conda_dir = conda_file_dir.split('lib')[0]
proj_lib = os.path.join(os.path.join(conda_dir, 'share'), 'proj')
os.environ["PROJ_LIB"] = proj_lib

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from datetime import date
from geopy.geocoders import Nominatim
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt


def cities_map():
    #Add cities to the map (need conection to Internet)    
    more_cities = True
    cities = []
    
    while more_cities:
        control = input("¿Quieres añadir una ciudad en el mapa? [S]/N ")
        if control == "S" or control == "":
            city = input("Nombre de la ciudad en ingles: ")
            cities.append(city)
        else:
            more_cities = False    
    
    return cities


#funtion
def create_map(document, num, region, cities):
    
    #Document .nc to use
    if document == "":
        document = input("Nombre del archivo: ")
    
    if document[-3:-1] + document[-1] != ".nc":
        document += ".nc"
        
    
    date = document[20:28]
    
    analysis_component = document[13:19].replace('_', '')
    
    # Import netCDF data
    archive_ncd = Dataset(document, 'r')
    
    #Get the data to trace the map
    analysis_data = ""
    data_lat = "latitude"
    data_lon = "longitude"
    
    if analysis_component == "NO2":
        analysis_data = "nitrogendioxide_tropospheric_column"
        
    elif analysis_component == "SO2":
        analysis_data = "sulfurdioxide_total_vertical_column"
        
    elif analysis_component == "AERAI":
        analysis_data = "aerosol_index_340_380"
        
    elif analysis_component == "O3":
        analysis_data = "ozone_total_vertical_column"
        
    else:
        print("No se puede crear un mapa para el archivo introducido")
        exit()
        
    
    
    lat = archive_ncd.groups['PRODUCT'].variables[data_lat][0,:,:]
    lon = archive_ncd.groups['PRODUCT'].variables[data_lon][0,:,:]
    data_component = archive_ncd.groups['PRODUCT'].variables[analysis_data]
    
    unit = ""
    min_value = 0
    
    
    if analysis_component == "NO2":
        unit = "moleculas/cm2"
        data_component = data_component * data_component.multiplication_factor_to_convert_to_molecules_percm2
        max_value = 50 * 1e14
        analysis_data = "nitrogendioxide_tropospheric_column"
        
    elif analysis_component == "SO2":
        unit = "Unidad Dobson"
        data_component = data_component * data_component.multiplication_factor_to_convert_to_DU
        min_value = 1
        max_value = 20
        analysis_data = "sulfurdioxide_total_vertical_column"
        
    elif analysis_component == "AERAI":
        unit = ""
        max_value = 5
        min_value = -5
        analysis_data = "aerosol_index_340_380"
        
    elif analysis_component == "O3":
        unit = "Unidad Dobson"
        data_component = data_component * data_component.multiplication_factor_to_convert_to_DU
        min_value = 100
        max_value = 500
        analysis_data = "ozone_total_vertical_column"
        
        
    m = Basemap(projection = 'cyl', resolution = 'i', 
                llcrnrlat = -90, 
                urcrnrlat = 90,
                llcrnrlon = -180,
                urcrnrlon = 180)  
    
    
    
    m.drawcoastlines(linewidth = 1)
    m.drawcountries(linewidth = 1)
    
    
    
    cmap = plt.cm.get_cmap('jet')
    cmap.set_under('w')
    
    m.pcolormesh(lon, lat, data_component[0,:,:], latlon = True, vmin = min_value, vmax = max_value, cmap = cmap)
    color_bar = m.colorbar()
    color_bar.set_label(unit)
    plt.autoscale()
    
    
    #Set the size of the map
    
    coordinates = read_geojson('map.geojson').get("features")[0].get("geometry").get("coordinates")[0]
    
    lon_min = coordinates[0][0]
    lon_max = coordinates[1][0]  
    lat_min = coordinates[0][1]
    lat_max = coordinates[2][1]
    
    axes = plt.gca()
    axes.set_ylim([lat_min, lat_max])
    axes.set_xlim([lon_min, lon_max])
            
    
    geolocator = Nominatim(user_agent="sentinel5P_to_map")    
    
    for city in cities:
        location = geolocator.geocode(city)
        x,y = m(location.longitude, location.latitude)
        plt.plot(x, y, 'ko', markersize=2.5)
        plt.text(x, y+0.2, city, color = 'black', fontsize=12, ha="center", 
                 fontstyle='italic', fontweight = "bold")
    
    
    
    title = f"Niveles de {analysis_component} en {region} el {date[6:]}/{date[4:6]}/{date[0:4]}\n"
    
    plt.title(title)
    
    fig = plt.gcf()
   
    plt.show(block=False)
    
    save_picture = input("¿Quieres guardar la imagen? S/N ").upper()
    if save_picture == "S":        
        image_name = analysis_component+"_"+date+"_"+num+".jpg"
        fig.savefig(image_name)
        print("La imagen se ha guardado como: " + image_name)
        
    plt.close()
    
    
    
def user_create_date():
    age = int(input("Año: ")) 
    month = int(input("Mes: "))
    day = int(input("Dia: "))
    return date(age, month, day)
    
#Component to study
component = input("¿Qué componente quiere estudiar? NO2, SO2, O3, AER: ").upper()
prodtype = ""

if component == "NO2":
    prodtype = "L2__NO2___"
elif component == "SO2":
    prodtype = "L2__SO2___"
elif component == "O3":
    prodtype = "L2__O3____"
elif component == "AER":
    prodtype = "L2__AER_AI"
    


#Place of observation
region = input("Lugar de estudio: ")

#Folder where the elements are
directory = input("Carpeta donde quieres guardar los archivos: ")

os.chdir(directory)




print("\nPeriodo de deteccion (introducir con numeros)")
print("Fecha inicio")

date_init = user_create_date()

print("\nFecha final")

date_end = user_create_date()



# connect to the API
api = SentinelAPI(user='s5pguest', password='s5pguest', 
                  api_url='https://s5phub.copernicus.eu/dhus/')


geojson_archive = input("Nombre del archivo .geojson que se va a utilizar: ")

# search by polygon, time, and Hub query keywords
footprint = geojson_to_wkt(read_geojson(geojson_archive))
products = api.query(area = footprint,date=(date_init, date_end),
                     platformname = 'Sentinel-5 Precursor', producttype = prodtype )

# download all results from the search
api.download_all(products)

cities = cities_map()

document = ""
num_document = 1

product = products.items()

for prod in product:
    document = prod[1].get("filename")
    create_map(document, f"{num_document}",region, cities)
    num_document += 1


