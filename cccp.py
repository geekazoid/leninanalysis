#!/usr/bin/env python
# coding: utf-8
import sys
import config
import argparse
import subprocess

import ming

from commands.database import reset_senses
from commands.year_analysis import calculate_year_analysis
from commands.top_senses_tables import create_tables
from commands.wget import wget

reload(config)


# Scraps ALL the works
def scrap_all_works():
    ret = subprocess.call("scrapy crawl lenin -o lenin_work.json -t json", shell=True)
    print "Scrapy has returned %s" % ret


def set_number_of_tokens():
    from includes.tokenizer import tokenize
    from pymongo import MongoClient
    client = MongoClient()
    db = client[config.DATABASE_NAME]

    for document in db.document.find():
        document['number_of_words'] = len(tokenize(document['text']))
        db.document.save(document)


def drop_iv():
    from pymongo import MongoClient
    client = MongoClient()
    print "Dropping IV results"
    db = client.lenin
    db.drop_collection('information_value_result')


def add_commands(parser):
    import analyzers.commands

    analyzers.commands.load_commands(parser)


def main():
    parser = argparse.ArgumentParser(description='Central de Control de Comandos y Procesos para el TP de Analisis de Lenin.')

    # Parameter to scrap all the works before or not
    parser.add_argument('--shell', action='store_true', default=False, help="Opens an ipython console with db configured")
    parser.add_argument('--scrap', action='store_true', default=False, help='Scraps all the Lenin Works')
    parser.add_argument('--populate-database', action='store_true', default=False, help="From the scrapped works creates database called \"lenin\" (it assumes you're running MongoDB at localhost)")
    parser.add_argument('--year-analysis', action='store_true', default=False, help="Calculate year analysis for each year between min-year and max-year")
    parser.add_argument('--plot', action='store_true', default=False, help="Add this flag for plotting")
    parser.add_argument('--drop-iv', action='store_true', default=False, help="Drop Information Value Results")
    parser.add_argument('--analysis', action='store_true', default=False, help="Add this flag for results calculation")
    parser.add_argument('--analysis-store-only-best', action='store_true', default=False, help="Add this flag for results calculation storing only the best result")
    parser.add_argument('--plot-iv-analysis', action='store_true', default=False, help="Shows some plot about Information Value Analysis")
    parser.add_argument('--plot-works', action='store_true', default=False, help="Plot corpus information")
    parser.add_argument('--window_size_generator', default='WindowsHardCodedSizeGenerator', help="Select a Window Size generator Algorhitm")
    parser.add_argument('--calculate-results', action='store_true', default=False, help="Calculate Information Value Results for Documents")
    parser.add_argument('--documents', nargs='+', metavar=('name'), help='Selects documents from name regex')
    parser.add_argument('--concepts', nargs='+', metavar=('word'), help='Selects concepts to print (works with --plot)')
    parser.add_argument('--min', metavar=('year'), help='year to start plot (works with --plot, default=1899)')
    parser.add_argument('--max', metavar=('year'), help='year to end plot (works with --plot, default=1923)')
    parser.add_argument('--notebook-server', action='store_true', default=False, help='Starts notebook server')
    parser.add_argument('--set-number-of-tokens', action='store_true', default=False, help='Calculate number of words for each work')
    parser.add_argument('--analyze-documents', action='store_true', default=False, help="Do Document Analysis for given concepts (pass with --concepts)")
    parser.add_argument('--reset-senses', action='store_true', default=False, help="Reset all senses calculated")
    parser.add_argument('--latex-info', action='store_true', default=False, help="Creates LaTex information for paper")
    parser.add_argument('--wget', metavar=('url'), help="Fetches the url and creates a Document")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    # Parse args
    args = parser.parse_args()

    if args.scrap:
        scrap_all_works()
    if args.populate_database:
        from commands.database import populate_database
        populate_database()
    if args.plot_iv_analysis:
        from plot.window_sizes import plot_iv_things
        plot_iv_things()
    if args.calculate_results:
        from commands.database import calculate_results
        calculate_results()

    if args.plot_works:
        from plot import works_plots
        works_plots.plot_all()

    doc_list = None
    if args.documents:
        from interpreter import Document
        doc_list = Document.query.find({"name": {"$regex": args.documents[0]}})
        #from information_value.models import DocumentList
        #doc_list = DocumentList(args.documents[0])

    if args.drop_iv:
        drop_iv()

    if args.analysis:
        from commands.database import calculate_results
        documents = None
        if doc_list is not None:
            documents = doc_list
        calculate_results(documents=documents, window_size_algorithm=args.window_size_generator, store_only_best=False)
    if args.analysis_store_only_best:

        from commands.database import calculate_results
        documents = None
        if doc_list:
            documents = doc_list.documents
        calculate_results(documents=documents, window_size_algorithm=args.window_size_generator, store_only_best=True)

    if args.plot:
        from plot import wn_plots
        import analyzers.synset_analyzer as wa

        concepts = None
        if args.concepts:
            concepts = args.concepts

        year_min = int(args.min) if args.min else 1899
        year_max = int(args.max) if args.max else 1923

        data = wa.year_vs_concept_data(concepts, year_min, year_max)
        wn_plots.plot_year_vs_concept_value(data)

    if args.year_analysis:

        concepts = ["war", "idealism", "revolution", "philosophy"]
        if args.concepts:
            concepts = args.concepts

        min_year = int(args.min) if args.min else 1899
        max_year = int(args.max) if args.max else 1923

        calculate_year_analysis(min_year, max_year, concepts)
    if args.notebook_server:
        subprocess.call("PYTHONPATH=$PYTHONPATH:$PWD; ipython notebook --notebook-dir=.", shell=True)
    if args.shell:
        subprocess.call("ipython -i interpreter.py", shell=True)
    if args.reset_senses:
        reset_senses()
    if args.latex_info:
        create_tables(doc_list)
    if args.wget:
        wget(args.wget)

    if args.set_number_of_tokens:
        set_number_of_tokens()

    if args.analyze_documents:
        import analyzers.commands
        concepts = ["war", "idealism", "revolution", "philosophy"]
        if args.concepts:
            concepts = args.concepts
        analyzers.commands.analyze_documents(concepts)

if __name__ == "__main__":
    ming_config = {'ming.document_store.uri': config.DATABASE_URL}
    ming.configure(**ming_config)

    from interpreter import init_logging
    init_logging()
    main()
