from typing import Final, Dict
import logfire
import tomli

def scrubbing_callback(m: logfire.ScrubMatch):
    if (
        m.path == ('message', 'e')
        and (m.pattern_match.group(0) == 'session' or m.pattern_match.group(0) == 'legislative_session')
    ):
        return m.value

    if (
        m.path == ('attributes', 'e')
        and (m.pattern_match.group(0) == 'session' or m.pattern_match.group(0) == 'legislative_session')
    ):
        return m.value

logfire.configure(scrubbing=logfire.ScrubbingOptions(callback=scrubbing_callback))
logfire.instrument_system_metrics({
    'process.runtime.cpu.utilization': None,  
    'system.cpu.simple_utilization': None,  
    'system.memory.utilization': ['available'],  
    'system.swap.utilization': ['used'],  
})

CONFIG: Final[Dict] = tomli.load(open("./tlo_urls.toml", 'rb'))