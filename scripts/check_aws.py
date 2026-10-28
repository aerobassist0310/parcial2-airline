"""Inventario de solo lectura, no crea ni detiene recursos."""
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--settings',default='aws-settings.json')
a=p.parse_args();s=json.loads(Path(a.settings).read_text())
import boto3
session=boto3.Session(region_name=s['region'])
def probe(label, fn):
    try: print(label, json.dumps(fn(),default=str,ensure_ascii=False))
    except Exception as e: print(label,'NO VERIFICADO',str(e))
probe('Identidad', lambda:session.client('sts').get_caller_identity())
probe('RDS', lambda:[{'id':d['DBInstanceIdentifier'],'clase':d['DBInstanceClass'],'multi_az':d['MultiAZ'],'estado':d['DBInstanceStatus']}
    for d in session.client('rds').describe_db_instances()['DBInstances']])
probe('EMR activo', lambda:session.client('emr').list_clusters(ClusterStates=['STARTING','BOOTSTRAPPING','RUNNING','WAITING','TERMINATING'])['Clusters'])
probe('EC2 activo', lambda:[{'id':i['InstanceId'],'tipo':i['InstanceType']} for r in session.client('ec2').describe_instances(Filters=[{'Name':'instance-state-name','Values':['running','pending']}])['Reservations'] for i in r['Instances']])
probe('NAT', lambda:session.client('ec2').describe_nat_gateways(Filter=[{'Name':'state','Values':['available','pending']}])['NatGateways'])
