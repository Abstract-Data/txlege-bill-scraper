import logfire

def scrubbing_callback(m: logfire.ScrubMatch):
    if (
        m.path == ('message', 'e')
        and m.pattern_match.group(0) == 'session'
    ):
        return m.value

    if (
        m.path == ('attributes', 'e')
        and m.pattern_match.group(0) == 'session'
    ):
        return m.value

logfire.configure(scrubbing=logfire.ScrubbingOptions(callback=scrubbing_callback))
logfire.instrument_system_metrics({
    'process.runtime.cpu.utilization': None,  
    'system.cpu.simple_utilization': None,  
    'system.memory.utilization': ['available'],  
    'system.swap.utilization': ['used'],  
})
