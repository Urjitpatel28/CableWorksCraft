using System;
using System.Collections.Generic;
using System.Configuration;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Windows;
using WpfUI.ViewModels;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
using MessageBox = System.Windows.MessageBox;

namespace WpfUI.Command
{
    public class CreateProjectCommand : BaseCommand
    {
        private readonly MainViewModel _viewModel;

        public CreateProjectCommand(MainViewModel viewModel)
        {
            _viewModel = viewModel;
        }

        public override bool CanExecute(object parameter)
        {
            //bool result = _viewModel?.ProjectDetails.projectName != null;
            //Debug.WriteLine("CanExecute called: " + result);
            //return result;
            return true;
        }

        public override void Execute(object parameter)
        {
            try
            {
                _viewModel.LodingWheelVisibility = Visibility.Visible;
                Mouse.OverrideCursor = System.Windows.Input.Cursors.Wait;  // Set cursor to busy
                _viewModel.StatusMessage = "Setting up folder directory and configuring layer parameters...";

                if(_viewModel.ProjectDetails.projectName == null)
                {
                    MessageBox.Show("Please enter a project name.", "Project Name Required", MessageBoxButton.OK, MessageBoxImage.Warning);
                    _viewModel.StatusMessage = "Please enter a project name.";
                    return;
                }

                if (_viewModel.ProjectDetails.cableCoreType == null)
                {
                    MessageBox.Show("Please select core type.", "Core Type Required", MessageBoxButton.OK, MessageBoxImage.Warning);
                    _viewModel.StatusMessage = "Please select core type.";
                    return;
                }               

                var projectFolderPath = _viewModel.ProjectDetails.projectName;

                string outputPath = Path.Combine(_viewModel.ProjectRootPath, projectFolderPath, "Outputs");

                // Check if the directory exists
                if (Directory.Exists(outputPath))
                {
                    // Prompt the user with a MessageBox to ask for overwrite permission
                    var folderExistResult = MessageBox.Show(
                        "Hey there! Looks like this folder already exists.\nWant to go ahead and overwrite the project?",
                        "File already exists!",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Question);

                    // If the user chooses 'No', exit the method
                    if (folderExistResult == MessageBoxResult.No)
                    {                        
                        return;
                    }

                    // If the user chooses 'Yes', try to delete the directory
                    if (folderExistResult == MessageBoxResult.Yes)
                    {
                        try
                        {
                            Directory.Delete(outputPath, true);
                        }
                        catch (Exception ex) 
                        {
                            // If deletion fails, just skip it and continue. Optionally log the error.
                            _viewModel.StatusMessage= $"Failed to delete directory : {ex}" ;
                        }
                    }
                }

                // Create the directory after deleting the old one or if it didn't exist
                Directory.CreateDirectory(outputPath);

                _viewModel.StatusMessage = "Project created! Time to configure your model.";

                // Enable the CableInfo stack panel
                System.Windows.Application.Current.Dispatcher.Invoke(() => _viewModel.CableInfoPanelEnabled = true);
            }
            finally
            {
                _viewModel.LodingWheelVisibility = Visibility.Hidden;
                Mouse.OverrideCursor = null;  // Reset cursor to default
            }
        }
    }
}
