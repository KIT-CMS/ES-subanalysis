# -*- coding: utf-8 -*-

import ROOT
import sys
import glob
import os

import subprocess
import pprint
pp = pprint.PrettyPrinter(indent=4)

import tempfile
import hashlib
import time

"""List all the pipelines to touch and the cuts"""
cut_dict = {
    "et_nominal": "(iso_1<0.15)*(byLooseIsolationMVArun2017v2DBoldDMwLT2017_2>0.5)*(njets==0)",  # ? (iso_1<0.15)
    # "et_nominal" : "(flagMETFilter == 1)*(extraelec_veto<0.5)*(extramuon_veto<0.5)*(dilepton_veto<0.5)*(againstMuonLoose3_2>0.5)*(againstElectronTightMVA6_2>0.5)*(byVLooseIsolationMVArun2017v2DBoldDMwLT2017_2>0.5)*(iso_1<0.15)",
    # "mt_nominal" : "(flagMETFilter == 1)*(extraelec_veto<0.5)*(extramuon_veto<0.5)*(dilepton_veto<0.5)*(againstMuonTight3_2>0.5)*(againstElectronVLooseMVA6_2>0.5)*(byVLooseIsolationMVArun2017v2DBoldDMwLT2017_2>0.5)*(iso_1<0.15)",
    # "tt_nominal" : "(flagMETFilter == 1)*(extraelec_veto<0.5)*(extramuon_veto<0.5)*(dilepton_veto<0.5)*(againstMuonLoose3_1>0.5 && againstMuonLoose3_2>0.5)*(againstElectronVLooseMVA6_1>0.5 && againstElectronVLooseMVA6_2>0.5)*(byVLooseIsolationMVArun2017v2DBoldDMwLT2017_1>0.5)*(byVLooseIsolationMVArun2017v2DBoldDMwLT2017_2>0.5)*(pt_1 > 40.0 && pt_2 > 40.0)",
    # "em_nominal" : "(flagMETFilter == 1)*(extraelec_veto<0.5)*(extramuon_veto<0.5)*(dilepton_veto<0.5)*(iso_1<0.15)*(iso_2<0.2)",
}

check_samples = True


def checkDirExists(path="", critical=False):
    if not os.path.isdir(path):
        if critical:
            print "Path ", path, "... does not exist"
            exit(1)
        else:
            return False
    return True


def getStandartizeDirectory(path="", exists=True):  # exists=True - critical to exist
    checkDirExists(path, critical=exists)
    if len(path) > 0 and path[-1] != "/":
        path += "/"
    return path


def dprint(*text):
    # if self.args.debug and text is not None:
    for t in text:
        print t,
    print


def dpprint(*text):
    # if self.args.debug and text is not None:
    for t in text:
        pp.pprint(t)


def yesORno(question):
    reply = str(raw_input(question + ' (y/n): ')).lower().strip()
    if len(reply) == 0:
        return yesORno("Uhhhh... please enter explicitle")
    elif reply[0].lower() == 'y':
        return True
    elif reply[0].lower() == 'n':
        return False
    else:
        return yesORno("Uhhhh... please enter ")


def execCommand(bash_command=None, question="\nStart execution?", force_yes=False, dry=False, yes_on_command=False):
    if bash_command is None:
        print "execCommand has no command"
        exit(1)
    if not dry:
        print "\nExecuting:", bash_command
        if force_yes or yes_on_command or yesORno(question):
            process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            if len(output) > 0:
                dprint("\texecCommand::output:", output)
            if error is not None:
                print "\texecCommand::error:", error
                exit(1)
        else:
            print "Executing declined"
    else:
        print "# Would call command:\n\t", bash_command


def prepareOutputDir(output, dry=False, recreate=False):
    print "\nOutput directory:", output

    if checkDirExists(output):
        dprint("Output dir exists")
        if len(os.listdir(output)) != 0:
            execCommand(bash_command="rm -rf " + output,
                question="The output directory Exists. " +
                    (len(os.listdir(output)) != 0) *
                    ("And is not empty (" + str(len(os.listdir(output))) + "). ") + "Would you like to delete it?: [y/n]",
                force_yes=recreate)

    if not checkDirExists(output):
        execCommand(bash_command="mkdir --parents " + output,
            question="The output directory does not yet exist. Would you like to create it?: [y/n]",
            force_yes=recreate)

    output = getStandartizeDirectory(output, exists=(False if dry else True))


def main():
    if check_samples:
        list_to_repeat = []

        common_path = '/nfs/dust/cms/user/glusheno/htautau/artus/ETauFakeES/skim_october/'
        original_dir = 'merged_samples'
        output_dir = '_'.join([original_dir, 'postsync'])

        for file_path in sorted(glob.glob(os.path.join(common_path, original_dir, "*/*.root"))):

            nick = os.path.basename(file_path).replace('.root', '')
            print 'nick:', nick

            input_file = ROOT.TFile.Open(file_path, 'read')
            print 'output file:', file_path.replace(original_dir, output_dir)
            exit(1)
            output_file = ROOT.TFile.Open(file_path.replace(original_dir, output_dir), 'read')

            count_failed = 0
            for pipeline in cut_dict:
                input_entries = input_file.Get(pipeline).Get("ntuple").GetEntries(cut_dict[pipeline])
                output_entries = output_file.Get(pipeline).Get("ntuple").GetEntries()
                if int(input_entries) != int(output_entries):
                    print "\033[91m\t Changed:", pipeline, "expected:", input_entries, "output:", output_entries, "\033[0m"
                    count_failed += 1
                else:
                    print "\033[92m\t Unchanged:", pipeline, "expected:", input_entries, "output:", output_entries, "\033[0m"

            if count_failed > 0:
                list_to_repeat.append(file_path)

        print "files to repeat:"
        for file_path in list_to_repeat:
            print file_path
    else:
        input_file_path = sys.argv[1]

        prepareOutputDir('post_sync/')

        output = 'temp_post_sync/' + input_file_path.split('/')[-1]
        print 'output:', output
        if os.path.exists(output):
            if yesORno('File already exists. Recreate? [y/n]'):
                output_file = ROOT.TFile(output, 'recreate')
            else:
                print "Executing declined"
                exit(1)
        else:
            print 'File does not yet exist'
            output_file = ROOT.TFile(output, 'recreate')
            if not os.path.exists(output):
                print 'Something went wrong'
                exit(1)

        print '\n Reading input file:', 'file://' + input_file_path
        input_file = ROOT.TFile.Open('file://' + input_file_path, 'read')

        for pipeline in cut_dict:
            print '\n\t pipeline:', pipeline
            output_file.mkdir(pipeline)
            output_file.cd(pipeline)
            oldtree = input_file.Get(pipeline).Get('ntuple')
            newtree = oldtree.CopyTree(cut_dict[pipeline])
            print pipeline, ': original - ', oldtree.GetEntries(), ', postsync - ', newtree.GetEntries()
            newtree.Write('', ROOT.TObject.kOverwrite)

    print 'end'


if __name__ == '__main__':
    main()
