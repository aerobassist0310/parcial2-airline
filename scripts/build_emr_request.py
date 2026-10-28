import argparse, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--settings', default='aws-settings.json')
p.add_argument('--out', default='emr-request.json')
a=p.parse_args();s=json.loads(Path(a.settings).read_text())
required=['bucket','emr_release_label','subnet_id','emr_service_role','emr_ec2_instance_profile','master_security_group','core_security_group']
for key in required:
    if not s.get(key) or 'CAMBIAR' in s[key]:
        raise SystemExit(f'Completar {key} con un valor real del laboratorio')
bucket=s['bucket']; prefix=s['data_prefix'].strip('/')
instances={'KeepJobFlowAliveWhenNoSteps':False,'TerminationProtected':False,
    'Ec2SubnetId':s['subnet_id'],
    'EmrManagedMasterSecurityGroup':s['master_security_group'],
    'EmrManagedSlaveSecurityGroup':s['core_security_group'],
    'InstanceGroups':[
        {'Name':'Primary','Market':'ON_DEMAND','InstanceRole':'MASTER','InstanceType':'m4.large','InstanceCount':1},
        {'Name':'Core','Market':'ON_DEMAND','InstanceRole':'CORE','InstanceType':'m4.large','InstanceCount':1}]}
if s.get('ec2_key_name'):instances['Ec2KeyName']=s['ec2_key_name']
# Modo client y memoria explícita: con un solo nodo core, en modo cluster el driver deja sin
# memoria YARN al ejecutor y el trabajo queda en RUNNING sin avanzar.
args=['spark-submit','--deploy-mode','client','--driver-memory','1g','--executor-memory','2g',
      '--executor-cores','1','--num-executors','1','--conf','spark.dynamicAllocation.enabled=false',
      f's3://{bucket}/code/etl_occupancy.py',
      '--flights',f's3://{bucket}/{prefix}/raw/flights.csv',
      '--reservations',f's3://{bucket}/{prefix}/raw/reservations.csv',
      '--detail-out',f's3://{bucket}/{prefix}/curated/reservations_curated/',
      '--metrics-out',f's3://{bucket}/{prefix}/metrics/route_month_metrics/']
request={'Name':f'airline-parcial2-{prefix}', 'ReleaseLabel':s['emr_release_label'],
 'Applications':[{'Name':'Spark'}],'Instances':instances,
 'JobFlowRole':s['emr_ec2_instance_profile'],'ServiceRole':s['emr_service_role'],
 'LogUri':f's3://{bucket}/emr-logs/', 'VisibleToAllUsers':True,
 'Steps':[{'Name':'curacion-ocupacion','ActionOnFailure':'TERMINATE_CLUSTER',
           'HadoopJarStep':{'Jar':'command-runner.jar','Args':args}}],
 'Tags':[{'Key':'Project','Value':'Parcial2'}]}
Path(a.out).write_text(json.dumps(request,indent=2),encoding='utf-8')
print(f'Archivo generado: {a.out}. NO se ha creado un clúster.')
print(f'REVISAR costo: 2 nodos m4.large. Región prevista: {s["region"]}.')
print(f'Crear solo tras revisar: aws emr create-cluster --region {s["region"]} --cli-input-json file://{a.out}')
