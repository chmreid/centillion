from whoosh.analysis import StemmingAnalyzer, LowercaseFilter  # StopFilter


def get_stemming_analyzer():
    stemming_analyzer = StemmingAnalyzer() | LowercaseFilter()
    return stemming_analyzer
