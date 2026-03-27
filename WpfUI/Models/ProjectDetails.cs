using System.ComponentModel;
using System.Windows.Input;

namespace WpfUI.Models
{
    public class ProjectDetails
    {
        private string _projectName;
        public string projectName
        {
            get => _projectName;
            set
            {
                if (_projectName != value)
                {
                    _projectName = value;
                    OnPropertyChanged(nameof(projectName));
                    //CommandManager.InvalidateRequerySuggested();
                }
            }
        }

        private string _cableCoreType;
        public string cableCoreType
        {
            get => _cableCoreType;
            set
            {
                if (_cableCoreType != value)
                {
                    _cableCoreType = value;
                    OnPropertyChanged(nameof(cableCoreType));
                }
            }
        }

        private CableParameters _parameters;
        public CableParameters parameters
        {
            get => _parameters;
            set
            {
                _parameters = value;
                OnPropertyChanged(nameof(parameters));
            }
        }

        private string _outputFile;
        public string outputFile
        {
            get => _outputFile;
            set
            {
                _outputFile = value;
                OnPropertyChanged(nameof(outputFile));
            }
        }

        private string _logFile;
        public string logFile
        {
            get => _logFile;
            set
            {
                _logFile = value;
                OnPropertyChanged(nameof(logFile));
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;
        private void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}