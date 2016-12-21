from db_commands import Panels
import panel_pal_db_setup

#panel_pal_db_setup.main()

p = Panels()
#p.import_pref_transcripts('NGD', '/results/Analysis/MiSeq/MasterTranscripts/NGD_preferred_transcripts.txt')
#p.import_pref_transcripts('CTD', '/results/Analysis/MiSeq/MasterTranscripts/CTD_preferred_transcripts.txt')
#p.import_pref_transcripts('IEM', '/results/Analysis/MiSeq/MasterTranscripts/IEM_preferred_transcripts.txt')
#p.import_pref_transcripts('Haems', '/results/Analysis/MiSeq/MasterTranscripts/Haems_preferred_transcripts.txt')
#p.import_pref_transcripts('HeredCancer', '/results/Analysis/MiSeq/MasterTranscripts/HeredCancer_preferred_transcripts.txt')
#p.import_bed('NGD', 'HSPRecessive', '/home/bioinfo/Natalie/wc/genes/NGD_HSPrecessive_v1.txt', '/results/Analysis/MiSeq/MasterBED/NGD_HSPrecessive_v1.bed', True)
#bed = p.export_bed('HSPRecessive', 'ROI_25')
#print bed
#p.compare_bed('/results/Analysis/MiSeq/MasterBED/NGD_HSPrecessive_v1.bed', False, bed)

#p.import_bed('NGD', 'Ataxia_Dystonia', '/home/bioinfo/Natalie/wc/genes/aptx.txt', '/home/bioinfo/Natalie/wc/genes/aptx.bed', True)

#print 'Ataxia_Dystonia'
p.import_bed('NGD','Ataxia_Dystonia','/home/bioinfo/Natalie/wc/genes/NGD_ataxia_dystonia_v3_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_ataxia_dystonia_v3_25bp.bed', True)
#bed = p.export_bed('Ataxia_Dystonia', 'ROI_25')
#p.compare_bed('/results/Analysis/MiSeq/MasterBED/NGD_ataxia_dystonia_v3_25bp.bed', False, bed)
#print 'Ataxia'
p.import_bed('NGD','Ataxia','/home/bioinfo/Natalie/wc/genes/NGD_ataxia_v4_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_ataxia_v4_25bp.bed', True)
#print 'Dystonia'
p.import_bed('NGD','Dystonia','/home/bioinfo/Natalie/wc/genes/NGD_dystonia_v3_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_dystonia_v3_25bp.bed', True)
#print 'DYT6'
#p.import_bed('NGD','DYT6','/home/bioinfo/Natalie/wc/genes/NGD_DYT6.txt','/results/Analysis/MiSeq/MasterBED/NGD_DYT6.bed', True)
#print 'EA_FHM'
p.import_bed('NGD','EA_FHM','/home/bioinfo/Natalie/wc/genes/NGD_EA_FHM_v4_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_EA_FHM_v4_25bp.bed', True)
#print 'EA'
p.import_bed('NGD','EA','/home/bioinfo/Natalie/wc/genes/NGD_EA_v3_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_EA_v3_25bp.bed', True)
#print 'FALS'
p.import_bed('NGD','FALS','/home/bioinfo/Natalie/wc/genes/NGD_FALS_v4_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_FALS_v4_25bp.bed', True)
#print 'FHM'
p.import_bed('NGD','FHM','/home/bioinfo/Natalie/wc/genes/NGD_FHM_v4_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_FHM_v4_25bp.bed', True)
#print 'HSPDominant'
p.import_bed('NGD','HSPDominant','/home/bioinfo/Natalie/wc/genes/NGD_HSPdominant_v1_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_HSPdominant_v1_25bp.bed', True)
#print 'HSPRecessive'
p.import_bed('NGD','HSPRecessive','/home/bioinfo/Natalie/wc/genes/NGD_HSPrecessive_v1.txt','/results/Analysis/MiSeq/MasterBED/NGD_HSPrecessive_v1.bed', True)
#print 'HSP'
p.import_bed('NGD','HSP','/home/bioinfo/Natalie/wc/genes/NGD_HSP_v4_25bp.txt','/results/Analysis/MiSeq/MasterBED/NGD_HSP_v4_25bp.bed', True)
#print 'Motor Dementia'
p.import_bed('NGD_Motor','Motor_Dementia','/home/bioinfo/Natalie/wc/genes/Motor_Dementia_v1.txt','/results/Analysis/MiSeq/MasterBED/Motor_Dementia_v1.bed', True)
#print 'Motor FALS'
p.import_bed('NGD_Motor','Motor_FALS','/home/bioinfo/Natalie/wc/genes/Motor_FALS_v2_25bp.txt','/results/Analysis/MiSeq/MasterBED/Motor_FALS_v2_25bp.bed', True)
#print 'Motor HSP'
p.import_bed('NGD_Motor','Motor_HSP','/home/bioinfo/Natalie/wc/genes/Motor_HSP_v2_25bp.txt','/results/Analysis/MiSeq/MasterBED/Motor_HSP_v2_25bp.bed', True)
#print 'Motor SMA'
p.import_bed('NGD_Motor','Motor_SMA','/home/bioinfo/Natalie/wc/genes/Motor_SMA_v1_25bp.txt','/results/Analysis/MiSeq/MasterBED/Motor_SMA_v1_25bp.bed', True)

p.import_bed('Haems_Bleeding','ADAMTS13','/home/bioinfo/Natalie/wc/genes/Bleeding_ADAMTS13_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_ADAMTS13_25_v1.bed', True)

p.import_bed('Haems_Bleeding','FactorV','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorV_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_FactorV_25_v1.bed', True)
p.import_bed('Haems_Bleeding','FactorVIII','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorVIII_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_FactorVIII_25_v1.bed', True)
p.import_bed('Haems_Bleeding','FactorVIII_IX','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorVIII_IX_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_FactorVIII_IX_25_v1.bed', True)
p.import_bed('Haems_Bleeding','FactorXIII','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorXIII_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_FactorXIII_25_v1.bed', True)
p.import_bed('Haems_Bleeding','Fibrinogen','/home/bioinfo/Natalie/wc/genes/Bleeding_Fibrinogen_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_Fibrinogen_25_v1.bed', True)
p.import_bed('Haems_Bleeding','Glanzman','/home/bioinfo/Natalie/wc/genes/Bleeding_Glanzman_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_Glanzman_25_v1.bed', True)
p.import_bed('Haems_Bleeding','MYH9','/home/bioinfo/Natalie/wc/genes/Bleeding_MYH9_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_MYH9_25_v1.bed', True)
p.import_bed('Haems_Bleeding','VWF','/home/bioinfo/Natalie/wc/genes/Bleeding_VWF_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_VWF_25_v1.bed', True)
p.import_bed('Haems_Bleeding','VWF_FVIII','/home/bioinfo/Natalie/wc/genes/Bleeding_VWF_FVIII_25_v1.txt','/results/Analysis/MiSeq/MasterBED/Bleeding_VWF_FVIII_25_v1.bed', True)
p.import_bed('Haems_BMF','DBA','/home/bioinfo/Natalie/wc/genes/Haems_DBA_25bp.txt','/results/Analysis/MiSeq/MasterBED/Haems_DBA_25bp.bed', True)
p.import_bed('Haems_BMF','DKC','/home/bioinfo/Natalie/wc/genes/Haems_DKC_25bp.txt','/results/Analysis/MiSeq/MasterBED/Haems_DKC_25bp.bed', True)
p.import_bed('Haems_BMF','Fanconi','/home/bioinfo/Natalie/wc/genes/Haems_Fanconi_25bp.txt','/results/Analysis/MiSeq/MasterBED/Haems_Fanconi_25bp.bed', True)
p.import_bed('Haems_BMF','MDS','/home/bioinfo/Natalie/wc/genes/Haems_MDS_25bp.txt','/results/Analysis/MiSeq/MasterBED/Haems_MDS_25bp.bed', True)
p.import_bed('Haems_BMF','SCN','/home/bioinfo/Natalie/wc/genes/Haems_SCN_25bp.txt','/results/Analysis/MiSeq/MasterBED/Haems_SCN_25bp.bed', True)
p.import_bed('Haems_BMF','TAR','/home/bioinfo/Natalie/wc/genes/Haems_TAR_25bp.txt','/results/Analysis/MiSeq/MasterBED/Haems_TAR_25bp.bed', True)
p.import_bed('Haems_TruSight','Fanconi','/home/bioinfo/Natalie/wc/genes/TruSight_Fanconi_25bp_v3.txt','/results/Analysis/MiSeq/MasterBED/TruSight_Fanconi_25bp_v3.bed', True)
p.import_bed('Haems_TruSight','Fanconi_FANCA','/home/bioinfo/Natalie/wc/genes/TruSight_Fanconi_FANCA_v2.txt','/results/Analysis/MiSeq/MasterBED/TruSight_Fanconi_FANCA_v2.bed', True)



