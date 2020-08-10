import arcpy
import pandas as pd

#LA Name 
LAName = 'Test'

#Setup
aprx = arcpy.mp.ArcGISProject('CURRENT')
arcpy.env.workspace = r'FilePath'.format(LAName)
map_ = aprx.listMaps('Map')[0]
layout = aprx.listLayouts('Layout')[0]
mf = layout.listElements('MapFrame_Element', 'Map Frame')[0]

#Wards
arcpy.MakeFeatureLayer_management(r"FilePath", 'WardsGB')
query = "LAD11NM = '{0}'".format(LAName) 
arcpy.SelectLayerByAttribute_management('WardsGB', 'NEW_SELECTION', query)
arcpy.CopyFeatures_management('WardsGB', 'Wards')
map_.removeLayer(
	map_.listLayers('WardsGB')[0]
)

#COAs
arcpy.MakeFeatureLayer_management(r'FilePath', 'COAsGB')
arcpy.TableToTable_conversion(
	r'FilePath'.format(LAName), 
	arcpy.env.workspace, 'pr_csv'
)
arcpy.AddJoin_management('COAsGB', 'OA11CD', 'pr_csv', 'COACode', join_type='KEEP_COMMON')
arcpy.CopyFeatures_management('COAsGB', 'COAs')
map_.removeLayer(
	map_.listLayers('COAsGB')[0]
)

#Lyr Files
lyrs = [lyr for lyr in map_.listLayers() if lyr.name != 'Wards' and lyr.name != 'Wards_style']
for lyr in lyrs: 
	lyr.updateConnectionProperties(
		lyr.connectionProperties, 
		map_.listLayers('COAs')[0].connectionProperties
	)

wards_style = map_.listLayers('Wards_style')[0]
wards_style.updateConnectionProperties(
	wards_style.connectionProperties,
	map_.listLayers('Wards')[0].connectionProperties
)

arcpy.TableToTable_conversion(
	r'FilePath'.format(LAName), arcpy.env.workspace, 
	'cvw_csv'
)
arcpy.AddJoin_management(
	'Private Rented (BRE Model)', 'COAs_OA11CD', 'cvw_csv', 'COACode', join_type='KEEP_COMMON'
)
arcpy.AddJoin_management(
	'Private Rented (Census 2011)', 'COAs_OA11CD', 'cvw_csv', 'COACode', join_type='KEEP_COMMON'
)

sym_dict = {
	'Private Rented (Census 2011)': 'cvw_csv.pc2011CensusPR', 'Private Rented (BRE Model)': 'cvw_csv.pcPrivateRentedModel', 
	'Low Income Households': 'pr_csv_pcLowIncome', 'Loft Insulation less than 100mm': 'pr_csv_pcLInsLT100', 
	'Average SimpleSAP': 'pr_csv_SimpleSAP', 'HHSRS Cat. 1 Hazards': 'pr_csv_pcHHSRS', 
	'HHSRS Excess Cold': 'pr_csv_pcExcessCold', 'HHSRS Falls Hazards': 'pr_csv_pcHHSRSFalls', 
	'Disrepair': 'pr_csv_pcDisrepair', 'Fuel Poverty 10%': 'pr_csv_pcFP10', 'Fuel Poverty LIHC': 'pr_csv_pcFPLIHC', 
	'Excess Cold and Low Income': 'pr_csv_pcECLI', 'EPC Rating F or G': 'pr_csv_pcEPCFG', 
	'Solid Walls': 'pr_csv_pcSolidWall', 'Insulated Cavity Walls': 'pr_csv_pcInsCavity', 
	'Un-insulated Cavity Walls': 'pr_csv_pcUninsCavity', 'Average Total Heat Demand': 'pr_csv_HeatDemand', 
	'Average Total Heat Cost': 'pr_csv_HeatCost', 'Average Total Energy Demand': 'pr_csv_EnergyDemand', 
	'Average Total Energy Cost': 'pr_csv_EnergyCost', 'Average Total Electricity Demand': 'pr_csv_ElectricityDemand', 
	'Average Total Electricity Cost': 'pr_csv_ElectricityCost'
}

for x in sym_dict:
	symbology = map_.listLayers(x)[0].symbology
	symbology.renderer.classificationField = sym_dict.get(x)
	map_.listLayers(x)[0].symbology = symbology

map_.removeLayer(
	map_.listLayers('Wards')[0]
)
map_.removeLayer(
	map_.listLayers('COAs')[0]
)

#Attribute Table 
arcpy.TableToTable_conversion(
	'Wards', r'FilePath'.format(LAName), 'AttributeTable.csv'
)
df = pd.read_csv(r'FilePath'.format(LAName))
df = df.loc[:, ['Ward_ID', 'WardName']].rename(
	columns={'Ward_ID': 'Ward ID', 'WardName': 'Ward Name'}
).sort_values(by='Ward ID', ascending=True)
df.to_csv(
	r'FilePath'.format(LAName), 
	index=False
)

extent = mf.getLayerExtent(wards_style)
mf.camera.setExtent(extent)
mf.camera.scale *= 1.1

#Exporting
for layer in map_.listLayers(): layer.visible = False
layers = [
	layer for layer in map_.listLayers() if layer.name != 'Wards_style' \
	and layer.name != 'OS Open Background'
]
for layer in layers:
	map_.listLayers('OS Open Background')[0].visible = True 
	wards_style.visible = True 
	layer.visible = True
	layout.exportToJPEG(
		r'FilePath'.format(LAName, layer.name)
		, resolution=170
	) 
	layer.visible = False
layout.exportToJPEG(r'FilePath'.format(LAName), resolution=170)