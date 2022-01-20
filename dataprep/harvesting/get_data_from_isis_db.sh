####
#
# Gera arquivos `*.seq`
#
#####
# BASES_ISOS_PATH=/path/bases/org.000/iso
BASES_ISOS_PATH=${1}

# BASE DE DADOS DE REFERENCIAS 
# campo v880: id do documento que contém as referências
# campo v65: data de publicação no formato YYYYMMDD
# campo v31: volume, se aplicável
# campo v32: número, subcampo ^s: contém suplemento, se aplicável
# campo v14: páginas, se aplicável
# campo v10: autor pessoa, subcampo ^s: sobrenome.
#            O formato `v10^s[1]` extrai o sobrenome do primeiro autor, se aplicável 
# campo v11: autor corporativo. O formato `v11[1]`, obtém o primeiro valor.
#
mx ${BASES_ISOS_PATH}/bib4cits lw=99999 "pft=v880,'|',v65,'|',v31,'|',v32,'|',v14,'|',v10^s[1],'|',v11[1],'|',v237,'|',v30,'|',(v12,' '),'|',v18,'|',v35,'|',v45,'|',v46,'|',v47,'|',v50,'|',v51,'|',v55,'|',v56,'|',v57,'|',v53,'|',v52,'|',v50,'|',v51,'|',v55,'|',v56,'|',v57,'|',v53,'|',v52,'|',v66,'|',v67,'|',v62,'|',v69,'|',v16[1],'|',v17[1],/" now > bib4cits.seq
tar cvfzp bib4cits.seq.tgz bib4cits.seq

mx ${BASES_ISOS_PATH}/artigos lw=9999 "pft=v880,'|',v881,'|',v35,'|',v65,'|',v31,'|',v32,'|',v131,v132,'|',v14,'|',v237,'|',replace(v702,'\','/'),'|',v71/" now > articles.seq
tar cvfzp articles.seq.tgz articles.seq

mx ${BASES_ISOS_PATH}/artigos lw=9999 "pft=(v880[1],'|',v12,'|',v65[1]*0.4/)" now > article_titles.seq
tar cvfzp article_titles.seq.tgz article_titles.seq

mx ${BASES_ISOS_PATH}/artigos lw=9999 "pft=(v880[1],'|',v83,'|',v65[1]*0.4/)" now > abstracts.seq
tar cvfzp abstracts.seq.tgz abstracts.seq

mx ${BASES_ISOS_PATH}/artigos lw=9999 "pft=(v880[1],'|',v85,'|',v65[1]*0.4/)" now > keywords.seq
tar cvfzp keywords.seq.tgz keywords.seq

mx iso=${BASES_ISOS_PATH}/tit.scl/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.sza/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.per/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.bol/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.arg/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.chl/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.col/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.cri/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.cub/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.esp/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.mex/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.prt/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.ven/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.pry/title.iso create=title now -all
mx title append=_title now -all
mx iso=${BASES_ISOS_PATH}/tit.ury/title.iso create=title now -all
mx title append=_title now -all


mx _title lw=9999 "pft=(v400[1],'|',v901/)" now > title_mission.seq
tar cvfzp title_mission.seq.tgz title_mission.seq

mx _title lw=9999 "pft=(v400[1],'|',v440/)" now > title_subj_description.seq
tar cvfzp title_subj_description.seq.tgz title_subj_description.seq

mx _title lw=9999 "pft=(v400[1],'|',v441/)" now > title_study_area.seq
tar cvfzp title_study_area.seq.tgz title_study_area.seq

mx _title lw=9999 "pft=(v400[1],'|',v854/)" now > title_subj_categories.seq
tar cvfzp title_subj_categories.seq.tgz title_subj_categories.seq

