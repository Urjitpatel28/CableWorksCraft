using System;
using System.IO;
using System.Windows;
using WpfUI.ViewModels;

namespace WpfUI.Command
{
    public class OpenProjectFolder : BaseCommand
    {
        private readonly MainViewModel _viewModel;

        public OpenProjectFolder(MainViewModel viewModel)
        {
            _viewModel = viewModel;
        }

        //public event EventHandler CanExecuteChanged;

        public override bool CanExecute(object parameter)
        {
            return true;
        }

        public override void Execute(object parameter)
        {
            try
            {

                //string rootPath = System.Configuration.ConfigurationManager.AppSettings["ServerRootPath"];

                string finalProjectPath = Path.Combine(_viewModel.ProjectRootPath, _viewModel.ProjectDetails.projectName, "Outputs");

                if (Directory.Exists(finalProjectPath))
                {
                    System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo()
                    {
                        FileName = finalProjectPath,
                        UseShellExecute = true,
                        Verb = "open"
                    });
                }
                else
                {
                    // Show a message to the user that the directory does not exist
                    MessageBox.Show("The directory does not exist.");
                }

            }
            catch (Exception ex)
            {

            }
        }
    }
}
