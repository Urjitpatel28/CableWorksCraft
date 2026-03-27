using System.Configuration;
using System.Diagnostics;
using System;
using System.Windows;
using WpfUI.Services;
using WpfUI.ViewModels;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.IO;
using System.Windows.Input; // For Cursors

namespace WpfUI.Command
{
    public class GenerateCommand : BaseCommand
    {
        private readonly MainViewModel _viewModel;
        private readonly Dictionary<double, double[]> LayerData;
        private bool _isExecuting = false;

        public GenerateCommand(MainViewModel viewModel)
        {
            _viewModel = viewModel;
            LayerData = Helpers.ExcelReader.ReadExcel(ConfigurationManager.AppSettings["CoreInLayersExcelPath"]);
            if (LayerData == null) { _viewModel.StatusMessage = "Unable to load CoreInLayers.xlxs"; }
        }

        public override bool CanExecute(object parameter)
        {
            // Check if ProjectDetails is valid, command isn't already executing, 
            // AND CableParameters has no validation errors
            return
                _viewModel?.ProjectDetails != null
                   && !_isExecuting
                   && _viewModel.ProjectDetails.parameters.spacing_1 != 0
                   && _viewModel.ProjectDetails.parameters.wire_dia != 0;              
                   
        }

        public override async void Execute(object parameter)
        {
            try
            {
                _viewModel.StatusMessage = "Creating model...";
                _isExecuting = true; // Block re-entry
                RaiseCanExecuteChanged();

                Application.Current.Dispatcher.Invoke(() =>
                    _viewModel.LodingWheelVisibility = Visibility.Visible);
                Mouse.OverrideCursor = Cursors.Wait;

                await Task.Run(() => GenerateFilesAndRunScript());

            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                _viewModel.StatusMessage = $"Error: {ex.Message}";
            }
            finally
            {
                Mouse.OverrideCursor = null;
                Application.Current.Dispatcher.Invoke(() =>
                    _viewModel.LodingWheelVisibility = Visibility.Hidden);
                _isExecuting = false;
                RaiseCanExecuteChanged();

            }
        }

        private void GenerateFilesAndRunScript()
        {
            //if (string.IsNullOrWhiteSpace(_viewModel.ProjectDetails.parameters.printingMatter))
            //{
            //    MessageBox.Show("Please fill in the 'Printing Matter' field before proceeding.", "Missing Information", MessageBoxButton.OK, MessageBoxImage.Warning);
            //    return;
            //}
            try
            {
                var jsonModel = _viewModel.ProjectDetails;

                string outputPath = Path.Combine(_viewModel.ProjectRootPath, jsonModel.projectName, "Outputs");
                Directory.CreateDirectory(outputPath);

                jsonModel.outputFile = Path.Combine(outputPath, $"{jsonModel.projectName}_{jsonModel.cableCoreType}.fcstd");

                if (File.Exists(jsonModel.outputFile))
                {
                    var fileExistResult = MessageBox.Show("Hey there! Looks like this folder already exists.\nWant to go ahead and overwrite the project?", "File already exists!", MessageBoxButton.YesNo, MessageBoxImage.Question);
                    if (fileExistResult == MessageBoxResult.No) return;                   
                }                   

                if (LayerData != null && LayerData.ContainsKey(jsonModel.parameters.numCylindersPerLayer))
                {
                    jsonModel.parameters.num_cylinders_per_layer = LayerData[jsonModel.parameters.numCylindersPerLayer];
                    foreach (double cylinder in jsonModel.parameters.num_cylinders_per_layer)
                    {
                        Debug.Print(cylinder.ToString());
                    }
                }

                switch (jsonModel.parameters.conductorMaterial?.ToLower()) // Use ToLower() to handle case insensitivity
                {
                    case "copper":
                        jsonModel.parameters.wireColor = "Brown";
                        break;

                    case "tinned":
                        jsonModel.parameters.wireColor = "Silver";
                        break;

                    case "aluminum":
                        jsonModel.parameters.wireColor = "Gray";
                        break;

                    default:
                        jsonModel.parameters.wireColor = "(0.8, 0.8, 0.8)";
                        break;
                }

                jsonModel.parameters.conductorScreenColor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.conductorScreenColor); //no need
                jsonModel.parameters.insulationColor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.insulationColor);
                jsonModel.parameters.nometallicScreenColor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.nometallicScreenColor);
                jsonModel.parameters.metallicScreenColor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.metallicScreenColor);
                jsonModel.parameters.idTapeColor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.idTapeColor);
                jsonModel.parameters.lappingColor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.lappingColor);
                jsonModel.parameters.wireColor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.wireColor);
                jsonModel.parameters.preinnersheathcolor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.preinnersheathcolor);
                jsonModel.parameters.innersheathcolor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.innersheathcolor);
                jsonModel.parameters.overinnersheathcolor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.overinnersheathcolor);
                jsonModel.parameters.armorcolor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.armorcolor);
                jsonModel.parameters.armortapingcolor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.armortapingcolor);
                jsonModel.parameters.outersheathcolor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.outersheathcolor);          
                jsonModel.parameters.condscreencolor1 = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.condscreencolor1);          
                jsonModel.parameters.condscreencolor2 = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.condscreencolor2);          
                jsonModel.parameters.condscreencolor3 = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.condscreencolor3);          
                jsonModel.parameters.condscreencolor4 = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.condscreencolor4);          
                jsonModel.parameters.condscreencolor5 = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.condscreencolor5);  
                jsonModel.parameters.halfcondscreencolor = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.halfcondscreencolor);  
                jsonModel.parameters.outercolor1 = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.outercolor1);
                jsonModel.parameters.outercolor2 = GetColorFromDictionary(_viewModel.ProjectDetails.parameters.outercolor2);                   
                

                jsonModel.logFile = Path.Combine(_viewModel.ProjectRootPath, jsonModel.projectName, $"{jsonModel.projectName}.log");

                string jsonFilePath = FileWriterService.SaveToJson(jsonModel, outputPath);

                string command = BuildCommand(jsonFilePath);
                ExecuteCommandAsAdmin(command);

                if (!File.Exists(jsonModel.outputFile))
                {
                    MessageBox.Show($"Fail to Create FreeCAD model", "Model Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    _viewModel.StatusMessage = $"Fail to Create FreeCAD model";
                    return;
                }

                double CalcRad = FileWriterService.ReadFromJson<double>(jsonFilePath, "$", "Calculated outer radius");

                _viewModel.ProjectDetails.parameters.leftoverDia = Math.Round(CalcRad, 2) * 2;

                Console.WriteLine($"layyd_dia: {_viewModel.ProjectDetails.parameters.leftoverDia}");

                MessageBox.Show("Data has been successfully saved", "Save Successful", MessageBoxButton.OK, MessageBoxImage.Information);

                // Confirmation to open the project folder
                var result = MessageBox.Show("Do you want to open the project folder?", "Open Folder", MessageBoxButton.YesNo, MessageBoxImage.Question);
                if (result == MessageBoxResult.Yes)
                {
                    OpenProjectFolder openFolderCommand = new OpenProjectFolder(_viewModel);
                    openFolderCommand.Execute(null);
                }
                _viewModel.StatusMessage = "Done";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"An error occurred while generating files and running the script: {ex.Message}", "Generation Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }


        private string GetColorFromDictionary(string colorKey)
        {
            if (colorKey!=null && _viewModel.ColorData.TryGetValue(colorKey, out var colorValue))
            {
                return colorValue;
            }
            else
            {
                return colorKey; // or some appropriate default
            }
        }


        private string BuildCommand(string jsonFilePath)
        {
            try
            {
                string pythonExePath = ConfigurationManager.AppSettings["PythonExePath"];

                string scriptPath = string.Empty;
                if (_viewModel.ProjectDetails.cableCoreType == "Circular")
                {
                    scriptPath = ConfigurationManager.AppSettings["CircularCoreScriptPath"];
                }
                else if (_viewModel.ProjectDetails.cableCoreType == "Shaped")
                {
                    scriptPath = ConfigurationManager.AppSettings["SectoralCoreScriptPath"];
                }

                if (scriptPath == string.Empty)
                {
                    MessageBox.Show($"Unable to find script for {_viewModel.ProjectDetails.cableCoreType} ",
                                                            "Script Error",
                                                            MessageBoxButton.OK,
                                                            MessageBoxImage.Error);
                    Environment.Exit(1);
                }

                return $@"""{pythonExePath}"" ""{scriptPath}"" --jsonFile ""{jsonFilePath}""";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"An error occurred while building the command: {ex.Message}", "Command Build Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return null;
            }

        }

        private void ExecuteCommandAsAdmin(string command)
        {
            try
            {
                ExecuteCommand executeCommand = new ExecuteCommand();
                executeCommand.RunCommandAsAdmin(command);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"An error occurred while executing the command as admin: {ex.Message}", "Execution Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
