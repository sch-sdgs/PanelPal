from db_commands import Panels


p = Panels()

p.import_pref_transcripts('NGD', '/results/Analysis/MiSeq/MasterTranscripts/NGD_preferred_transcripts.txt')
p.import_pref_transcripts('CTD', '/results/Analysis/MiSeq/MasterTranscripts/CTD_preferred_transcripts.txt')
p.import_pref_transcripts('IEM', '/results/Analysis/MiSeq/MasterTranscripts/IEM_preferred_transcripts.txt')
p.import_pref_transcripts('Haems', '/results/Analysis/MiSeq/MasterTranscripts/Haems_preferred_transcripts.txt')
p.import_pref_transcripts('HeredCancer', '/results/Analysis/MiSeq/MasterTranscripts/HeredCancer_preferred_transcripts.txt')
p.import_bed('NGD', 'HSPRecessive', '/home/bioinfo/Natalie/wc/genes/NGD_HSPrecessive_v1.txt')