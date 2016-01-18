import re


def parse_search_terms(raw_search_value):
    search_regexp = r'(?:[^\s,"]|"(?:\\.|[^"])*")+'  # splits by space, ignores space in quotes
    if not raw_search_value:
        return {}
    parsed_search = {}
    for query_part in re.findall(search_regexp, raw_search_value):
        if not query_part:
            continue
        if query_part.startswith('result:'):
            parsed_search['result'] = preprocess_search_value(query_part[len('result:'):])
        elif query_part.startswith('args:'):
            if 'args' not in parsed_search:
                parsed_search['args'] = []
            parsed_search['args'].append(preprocess_search_value(query_part[len('args:'):]))
        elif query_part.startswith('kwargs:'):
            if 'kwargs'not in parsed_search:
                parsed_search['kwargs'] = {}
            key, value = [p.strip() for p in query_part[len('kwargs:'):].split('=')]
            parsed_search['kwargs'][key] = preprocess_search_value(value)
        else:
            parsed_search['any'] = preprocess_search_value(query_part)
    return parsed_search


def satisfies_search_terms(task, any_value_search_term, result_search_term, args_search_terms, kwargs_search_terms):
    if not any([any_value_search_term, result_search_term, args_search_terms, kwargs_search_terms]):
        return True
    terms = [
        any_value_search_term and any_value_search_term in '|'.join(filter(None, ([task.args, task.kwargs, str(task.result)]))),
        result_search_term and result_search_term in task.result,
        kwargs_search_terms and all(
            stringified_dict_contains_value(k, v, task.kwargs) for k, v in kwargs_search_terms.items()
        ),
        args_search_terms and task_args_contains_search_args(task.args, args_search_terms)
    ]
    return any(terms)


def stringified_dict_contains_value(key, value, str_dict):
    """
        Checks if dict in for of string like "{'test': 5}" contains key/value pair.

        This works faster, then creating actual dict from string since this operation is called
        for each task in case of kwargs search.
    """
    value = str(value)
    try:
        key_index = str_dict.index(key) + len(key) + 3  # + 3 for key right quote, one for colon and one for space
    except ValueError:  # key not found
        return False
    try:
        comma_index = str_dict.index(',', key_index)
    except ValueError:  # last value in dict
        comma_index = str_dict.index('}', key_index)
    return str(value) == str_dict[key_index:comma_index].strip('"\'')


def preprocess_search_value(raw_value):
    return raw_value.strip('" ') if raw_value else ''


def task_args_contains_search_args(task_args, search_args):
    return all(a in task_args for a in search_args)
