import boto3

def _get_sts_client(role_arn, external_id):
    sts_client = boto3.client('sts')
    assumed_role = sts_client.assume_role(RoleArn=role_arn,
                                          RoleSessionName="cloudwatch",
                                          ExternalId=external_id)
    credentials=assumed_role['Credentials']
    return boto3.client('cloudwatch',
                        aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken'])

def _get_default_client():
    return boto3.client('cloudwatch')

def _get_client(args):
    if args.sts_role_arn is not None and args.sts_external_id is not None:
        return _get_sts_client(args.sts_role_arn, args.sts_external_id)
    else:
        return _get_default_client()

def _metric_suffix(s):
    return s.rsplit('.', 1)[1]

def _coerce_metric(k, v):
    if (k.startswith('cpu.')):
        # We don't expose CPU metrics through Cloudwatch, as this is already collected
        # by the regular metrics.
        return None
    elif (k == 'license.memory'):
        return ('Bytes', float(v))


    sufx = _metric_suffix(k)
    if sufx == 'total_ns':
        return ('Microseconds', float(v) / 1000)
    elif (sufx == 'duration_us' or
          sufx == 'time_us'):
        return ('Microseconds', float(v))
    elif (sufx == 'duration_ms' or
          sufx == 'time_ms'):
        return ('Milliseconds', float(v))
    elif (sufx == 'remaining_days'):
        return ('Seconds', float(v * 86400))
    elif (sufx == 'retry_wait_seconds'):
        return ('Seconds', float(v))
    elif (sufx.startswith('bytes') or sufx.endswith('bytes')):
        return ('Bytes', float(v))
    elif (sufx.endswith('count')):
        return ('Count', float(v))
    else:
        print('unknown suffix: ', sufx, ', k: ', k)
        return ('None', float(v))


def _to_metric(k, v):
    try:
        x = _coerce_metric(k, v)
        if x:
            (u, v_) = x
            return {'MetricName': k,
                    'Value': v_,
                    'Unit': u}
    except:
        return None


def _qdb_to_cloudwatch(stats):
    # We want to flatten all metrics into a tuple of 3 items:
    # - node_id
    # - user_id
    # - measurement

    ret = list()

    for node_id,xs in stats.items():
        for user_id,xs_ in xs['by_uid'].items():
            dims = [{'Name': 'UserId',
                     'Value': str(user_id)},
                    {'Name': 'NodeId',
                     'Value': str(node_id)}]

            for k,v in xs_.items():
                m = _to_metric(k, v)

                if m:
                    m['Dimensions'] = dims
                    ret.append(m)

        dims = [{'Name': 'NodeId',
                 'Value': str(node_id)}]

        for k,v in xs['cumulative'].items():
            m = _to_metric(k, v)

            if m:
                m['Dimensions'] = dims
                ret.append(m)


    return ret



def push_stats(stats, args):
    client = _get_client(args)
    stats_ = _qdb_to_cloudwatch(stats)


    metrics_per_req = 20
    metrics = [stats_[i:i+metrics_per_req] for i in range(0, len(stats_), metrics_per_req)]

    for metric in metrics:
        response = client.put_metric_data(Namespace=args.namespace,
                                          MetricData=metric)

    print("Pushed {} metrics".format(len(stats_)))
