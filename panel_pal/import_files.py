from db_commands import Panels
import panel_pal_db_setup

#panel_pal_db_setup.main()

p = Panels()
p.import_pref_transcripts('NGD', '/results/Analysis/MiSeq/MasterTranscripts/NGD_preferred_transcripts.txt')
p.import_pref_transcripts('CTD', '/results/Analysis/MiSeq/MasterTranscripts/CTD_preferred_transcripts.txt')
p.import_pref_transcripts('IEM', '/results/Analysis/MiSeq/MasterTranscripts/IEM_preferred_transcripts.txt')
p.import_pref_transcripts('Haems', '/results/Analysis/MiSeq/MasterTranscripts/Haems_preferred_transcripts.txt')
p.import_pref_transcripts('HeredCancer', '/results/Analysis/MiSeq/MasterTranscripts/HeredCancer_preferred_transcripts.txt')

p.import_bed('NGD', 'NGD', 'Ataxia_Dystonia','/home/bioinfo/Natalie/wc/genes/NGD_ataxia_dystonia_v3_25bp.txt', True)
p.import_bed('NGD', 'NGD', 'Ataxia','/home/bioinfo/Natalie/wc/genes/NGD_ataxia_v4_25bp.txt', True)
#print 'Dystonia'
p.import_bed('NGD', 'NGD', 'Dystonia','/home/bioinfo/Natalie/wc/genes/NGD_dystonia_v3_25bp.txt', True)
#print 'DYT6'
#p.import_bed('NGD','DYT6','/home/bioinfo/Natalie/wc/genes/NGD_DYT6.txt','/results/Analysis/MiSeq/MasterBED/NGD_DYT6.bed', True)
#print 'EA_FHM'
p.import_bed('NGD', 'NGD', 'EA_FHM','/home/bioinfo/Natalie/wc/genes/NGD_EA_FHM_v4_25bp.txt', True)
#print 'EA'
p.import_bed('NGD', 'NGD', 'EA','/home/bioinfo/Natalie/wc/genes/NGD_EA_v3_25bp.txt', True)
#print 'FALS'
p.import_bed('NGD', 'NGD', 'FALS','/home/bioinfo/Natalie/wc/genes/NGD_FALS_v4_25bp.txt', True)
#print 'FHM'
p.import_bed('NGD', 'NGD', 'FHM','/home/bioinfo/Natalie/wc/genes/NGD_FHM_v4_25bp.txt', True)
#print 'HSPDominant'
p.import_bed('NGD', 'NGD', 'HSPDominant','/home/bioinfo/Natalie/wc/genes/NGD_HSPdominant_v1_25bp.txt', True)
#print 'HSPRecessive'
p.import_bed('NGD', 'NGD', 'HSPRecessive','/home/bioinfo/Natalie/wc/genes/NGD_HSPrecessive_v1.txt', True)
#print 'HSP'
p.import_bed('NGD', 'NGD', 'HSP','/home/bioinfo/Natalie/wc/genes/NGD_HSP_v4_25bp.txt', True)
#print 'Motor Dementia'
p.import_bed('NGD','NGD_Motor', 'Motor_Dementia','/home/bioinfo/Natalie/wc/genes/Motor_Dementia_v1.txt', True)
#print 'Motor FALS'
p.import_bed('NGD','NGD_Motor', 'Motor_FALS','/home/bioinfo/Natalie/wc/genes/Motor_FALS_v2_25bp.txt', True)
#print 'Motor HSP'
p.import_bed('NGD','NGD_Motor','Motor_HSP','/home/bioinfo/Natalie/wc/genes/Motor_HSP_v2_25bp.txt', True)
#print 'Motor SMA'
p.import_bed('NGD','NGD_Motor','Motor_SMA','/home/bioinfo/Natalie/wc/genes/Motor_SMA_v1_25bp.txt', True)

p.import_bed('Haems','Haems_Bleeding','ADAMTS13','/home/bioinfo/Natalie/wc/genes/Bleeding_ADAMTS13_25_v1.txt', True)

p.import_bed('Haems','Haems_Bleeding','FactorV','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorV_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','FactorVIII','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorVIII_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','FactorVIII_IX','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorVIII_IX_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','FactorXIII','/home/bioinfo/Natalie/wc/genes/Bleeding_FactorXIII_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','Fibrinogen','/home/bioinfo/Natalie/wc/genes/Bleeding_Fibrinogen_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','Glanzman','/home/bioinfo/Natalie/wc/genes/Bleeding_Glanzman_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','MYH9','/home/bioinfo/Natalie/wc/genes/Bleeding_MYH9_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','VWF','/home/bioinfo/Natalie/wc/genes/Bleeding_VWF_25_v1.txt', True)
p.import_bed('Haems','Haems_Bleeding','VWF_FVIII','/home/bioinfo/Natalie/wc/genes/Bleeding_VWF_FVIII_25_v1.txt', True)
p.import_bed('Haems','Haems_BMF','DBA','/home/bioinfo/Natalie/wc/genes/Haems_DBA_25bp.txt', True)
p.import_bed('Haems','Haems_BMF','DKC','/home/bioinfo/Natalie/wc/genes/Haems_DKC_25bp.txt', True)
p.import_bed('Haems','Haems_BMF','Fanconi','/home/bioinfo/Natalie/wc/genes/Haems_Fanconi_25bp.txt', True)
p.import_bed('Haems','Haems_BMF','MDS','/home/bioinfo/Natalie/wc/genes/Haems_MDS_25bp.txt', True)
p.import_bed('Haems','Haems_BMF','SCN','/home/bioinfo/Natalie/wc/genes/Haems_SCN_25bp.txt', True)
p.import_bed('Haems','Haems_BMF','TAR','/home/bioinfo/Natalie/wc/genes/Haems_TAR_25bp.txt', True)
p.import_bed('Haems','Haems_TruSight','Fanconi','/home/bioinfo/Natalie/wc/genes/TruSight_Fanconi_25bp_v3.txt', True)
p.import_bed('Haems','Haems_TruSight','Fanconi_FANCA','/home/bioinfo/Natalie/wc/genes/TruSight_Fanconi_FANCA_v2.txt', True)



