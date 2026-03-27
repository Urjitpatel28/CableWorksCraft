using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Forms;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using WpfUI.ViewModels;

namespace WpfUI.Views
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();


            this.Closing += new System.ComponentModel.CancelEventHandler(MainWindow_Closing);

            var viewModel = DataContext as MainViewModel;

        }

        private void MainWindow_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            // Prompt the user to confirm closing
            MessageBoxResult result = System.Windows.MessageBox.Show("Do you really want to close the application?", "Confirmation", MessageBoxButton.YesNo, MessageBoxImage.Question);

            if (result == MessageBoxResult.No)
            {
                e.Cancel = true; // Cancel the closing
            }
            else
            {
                // Explicitly close all open child windows
                foreach (Window window in System.Windows.Application.Current.Windows)
                {
                    if (window != this) // Don't close the main window yet
                    {
                        window.Close();
                    }
                }
            }
        }
    }
}