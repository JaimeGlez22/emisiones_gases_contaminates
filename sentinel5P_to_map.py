
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


#Place of observation
region = input("Lugar de estudio: ")

#Folder where the elements are
directory = input("Direccion carpeta donde se encuentran los archivos: ")

os.chdir(directory)

#Document .nc to use
document = input("Nombre del archivo: ")

if document[-3:-1] + document[-1] != ".nc":
    document += ".nc"
    
#documento = "S5P_OFFL_L2__NO2____20200118T104330_20200118T122500_11734_01_010302_20200122T031557.nc"

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
data_component = archive_ncd.groups['PRODUCT'].variables[analysis_data][0, :, :]


unit = ""
max_value = 5
min_value = -5

if not analysis_component == "AERAI":
    fill_value = archive_ncd.groups['PRODUCT'].variables[analysis_data]._FillValue
    fill_val = fill_value*1000000

# Replacing the fill values/ missing values by 'nan'
    data_component_temp = np.array(data_component)*1000000
    data_component_temp[data_component_temp == fill_val] = np.nan
    data_component = data_component_temp
    
    max_value = 100
    min_value = 0
    
    unit = "μ.mol / m2"

 
    
    
m = Basemap(projection = 'cyl', resolution = 'i', 
            llcrnrlat = -90, 
            urcrnrlat = 90,
            llcrnrlon = -180,
            urcrnrlon = 180)  



m.drawcoastlines(linewidth = 1)
m.drawcountries(linewidth = 1)



cmap = plt.cm.get_cmap('jet')
cmap.set_under('w')

m.pcolormesh(lon, lat, data_component, latlon = True, vmin = min_value, vmax = max_value , cmap = cmap)
color_bar = m.colorbar()
color_bar.set_label(unit)
plt.autoscale()


#Establecer los valores maximos de latitud y de longitud que se representaran en el mapa
lat_max = int(input("latitud máxima: "))
lat_min = int(input("latitud minima: "))
lon_max = int(input("longitud maxima: "))
lon_min = int(input("longitud minima: "))

axes = plt.gca()
axes.set_ylim([lat_min, lat_max])
axes.set_xlim([lon_min, lon_max])


#Put cities in the map
from geopy.geocoders import Nominatim

more_cities = True
cities = []

while more_cities:
    control = input("¿Quieres añadir una ciudad en el mapa? S/N ")
    if control == "S":
        city = input("Nombre de la ciudad en ingles: ")
        cities.append(city)
    else:
        more_cities = False
        
    
print(cities)

#cities = ["Milano", "Lyon", "Monaco", "Venice", "Florence"]

geolocator = Nominatim(user_agent="JaimeGlez")


#Clon = [9.21, 4.84, 7.41, 12.31, 11.28]
#Clat = [45.46, 45.73, 43.74, 45.42, 43.76]

for city in cities:
    location = geolocator.geocode(city)
    x,y = m(location.longitude, location.latitude)
    plt.plot(x, y, 'ko', markersize=2.5)
    plt.text(x, y+0.2, city, color = 'black', fontsize=12, ha="center", 
             fontstyle='italic', fontweight = "bold")



title = f"Niveles de {analysis_component} en {region} el {date[6:]}/{date[4:6]}/{date[0:4]}"

plt.title(title)

fig = plt.gcf()
image_name = analysis_component+"_"+date+".jpg"
fig.savefig(image_name)

plt.show()


