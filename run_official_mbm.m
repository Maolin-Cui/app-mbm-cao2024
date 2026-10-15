% GROUP-LEVEL MATLAB wrapper around the original, unmodified Cao 2024 MBM.
% Requires real aligned fsLR-32k GIFTI thickness maps and the authors' exact
% matching 32k template eigenmodes, mass matrices, masks and vtk meshes.
% This file does not reimplement MBM statistics.

cfg = jsondecode(fileread('config.json'));
root = char(cfg.group_bundle);
assert(exist(fullfile('vendor','MBM','mbm_main.m'),'file') == 2, ...
    'The original official NSBLab/MBM toolbox is missing');
addpath(fullfile(pwd,'vendor','MBM'));

outDir = fullfile(pwd,'result');
if ~exist(outDir,'dir'), mkdir(outDir); end

hemiCodes = {'lh','rh'};
hemiLabels = {'left','right'};
for ix = 1:2
    hemi = hemiCodes{ix};
    MBM = struct();
    MBM.maps.anatListFile = fullfile(pwd,'prepared',[hemi '_input_maps.txt']);
    MBM.maps.maskFile = fullfile(root,'template',[hemi '.mask.txt']);
    MBM.stat.test = 'ANCOVA_Z';
    MBM.stat.designFile = fullfile(pwd,'prepared','design_ANCOVA.txt');
    MBM.stat.nPer = double(cfg.n_permutations);
    MBM.stat.pThr = double(cfg.gpd_p_threshold);
    MBM.stat.thres = double(cfg.p_threshold);
    MBM.stat.fdr = logical(cfg.fdr);
    MBM.eig.eigFile = fullfile(root,'template',[hemi '.eig.txt']);
    MBM.eig.massFile = fullfile(root,'template',[hemi '.mass.mat']);
    MBM.eig.nEigenmode = double(cfg.num_modes);
    MBM.eig.saveResult = true;
    MBM.eig.resultFile = fullfile(outDir,['official_MBM_' hemi '.mat']);
    MBM.plot.vtkFile = fullfile(root,'template',[hemi '.surf.vtk']);
    MBM.plot.visualize = false;
    MBM.plot.saveFig = false;
    MBM.plot.figFile = fullfile(outDir,['official_MBM_' hemi '.png']);
    MBM.plot.hemis = hemiLabels{ix};
    MBM.plot.nInfluentialMode = min(10,double(cfg.num_modes));
    fprintf('Running official MBM 2024: %s, %g modes, %g permutations\n', ...
        hemi, MBM.eig.nEigenmode, MBM.stat.nPer);
    MBM = mbm_main(MBM);
    assert(exist(MBM.eig.resultFile,'file')==2, ...
        'Official MBM did not create the expected results file');
    clear MBM
end
fprintf('Official MBM finished. Results in %s\n',outDir);
