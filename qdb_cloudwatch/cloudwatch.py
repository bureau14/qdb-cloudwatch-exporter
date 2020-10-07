import boto3

def _get_client():
    return boto3.client('cloudwatch')

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
    elif (sufx == 'remaining_days'):
        return ('Seconds', float(v * 86400))
    elif (sufx.startswith('bytes') or sufx.endswith('bytes')):
        return ('Bytes', float(v))
    elif (sufx.endswith('count')):
        return ('Count', float(v))
    else:
        print('unknown suffix: ', sufx, ', k: ', k, ', v: ', v)
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



def push_stats(stats, namespace):
    client = _get_client()
    stats_ = _qdb_to_cloudwatch(stats)


    metrics_per_req = 20
    metrics = [stats_[i:i+metrics_per_req] for i in range(0, len(stats_), metrics_per_req)]

    for metric in metrics:
        response = client.put_metric_data(Namespace=namespace,
                                          MetricData=metric)

    print("Pushed {} metrics".format(len(stats_)))
