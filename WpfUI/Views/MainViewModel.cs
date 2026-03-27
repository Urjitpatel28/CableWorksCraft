using ClosedXML.Excel;
using DocumentFormat.OpenXml.Office.CustomUI;
using DocumentFormat.OpenXml.Spreadsheet;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Configuration;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using WpfUI.Command;
using WpfUI.Helpers;
using WpfUI.Models;

namespace WpfUI.ViewModels
{
    public class MainViewModel : INotifyPropertyChanged
    {
        //Commands
        public BaseCommand GenerateCommand { get; set; }
        public BaseCommand CreateProjectCommand { get; set; }


        //All UI lists
        public ObservableCollection<string> CableCoreTypes { get; set; }
        public ObservableCollection<double> NumberOfCores { get; set; }
        public ObservableCollection<string> ConductorMaterialList { get; set; }
        public ObservableCollection<string> InsulationMaterialList { get; set; }
        public ObservableCollection<string> ConductorScreenMaterialList { get; set; }
        public ObservableCollection<int> NoOfLayersList { get; set; }
        public ObservableCollection<int> NoOfFillerList { get; set; }
        public ObservableCollection<string> FillingMethodList { get; set; }
        public ObservableCollection<string> FillerMaterialList { get; set; }
        public ObservableCollection<string> InsulationScreenMaterialList { get; set; }
        public ObservableCollection<string> InnerSheathMaterialList { get; set; }
        public ObservableCollection<string> InnerSheathColorList { get; set; }
        public ObservableCollection<string> ArmorTypeList { get; set; }
        public ObservableCollection<string> OuterSheathMaterialList { get; set; }
        public ObservableCollection<string> OuterSheathColorList { get; set; }


        // Dictionary to hold color names and RGB values
        public Dictionary<string, string> ColorData { get; private set; }

        // ObservableCollection for UI binding (e.g., ComboBox, ListView)
        public ObservableCollection<string> ColorList { get; set; } = new ObservableCollection<string>();
        public ObservableCollection<string> LayerColorList { get; set; } = new ObservableCollection<string>();


        public MainViewModel()
        {
            ProjectRootPath = GetProjectRootPathFromConfig();

            ProjectDetails = new ProjectDetails
            {
                parameters = new CableParameters()
            };

            CreateProjectCommand = new CreateProjectCommand(this);
            GenerateCommand = new GenerateCommand(this);

            //GenerateCommand = new RelayCommand(ExecuteGenerateCommand);

            #region UI lists
            CableCoreTypes = new ObservableCollection<string>
                                                            {
                                                                "Circular",
                                                                "Shaped"
                                                            };

            LayerColorList = new ObservableCollection<string>
                                                            {
                                                                "Black",
                                                                "White"
                                                            };



            //ConductorMaterialList = new ObservableCollection<string>
            //                                                {
            //                                                    "Copper",
            //                                                    "Aluminium",
            //                                                    "Tinned",
            //                                                    "(None)",

            //                                                };

            //InsulationMaterialList = new ObservableCollection<string>
            //                                                {
            //                                                    "XLPE",
            //                                                    "(None)",

            //                                                    //add more if any
            //                                                };

            //ConductorScreenMaterialList = new ObservableCollection<string>
            //                                                {
            //                                                    "Mico",
            //                                                    "Non-Metalic",
            //                                                    "Water Blocking",
            //                                                    "(None)",
            //                                                };

            FillingMethodList = new ObservableCollection<string>
                                                            {
                                                                "Auto",
                                                                "Manual",
                                                            };

            //FillerMaterialList = new ObservableCollection<string>
            //                                                {
            //                                                    "PP",
            //                                                    "XLPE",
            //                                                    "PVC",
            //                                                    "(None)",

            //                                                };

            //InsulationScreenMaterialList = new ObservableCollection<string>
            //                                                {
            //                                                    "Polyster",
            //                                                    "Fiber Glass",
            //                                                    "(None)",

            //                                                };

            //InnerSheathMaterialList = new ObservableCollection<string>
            //                                                {
            //                                                    "PVC",
            //                                                    "XLPE",
            //                                                    "HDPE",
            //                                                    "(None)",

            //                                                };

            //OuterSheathMaterialList = new ObservableCollection<string>
            //                                                {
            //                                                    "PVC",
            //                                                    "St1",
            //                                                };


            ArmorTypeList = new ObservableCollection<string>
                                                            {
                                                                "Wire",
                                                                "Strip",
                                                            };


            NumberOfCores = new ObservableCollection<double>();
            for (int i = 1; i <= 100; i++)
            {
                NumberOfCores.Add(i); // Adds integers from 1 to 100
            }

            // Add the decimal values
            NumberOfCores.Add(3.5);
            NumberOfCores.Add(4.5);
            NumberOfCores.Add(5.5);

            // Optional: Sort the collection if you need these values to be in numerical order
            var sortedCores = NumberOfCores.OrderBy(x => x).ToList();
            NumberOfCores.Clear();
            foreach (var core in sortedCores)
            {
                NumberOfCores.Add(core);
            }

            NoOfLayersList = new ObservableCollection<int>();
            for (int i = 0; i <= 3; i++)
            {
                NoOfLayersList.Add(i);
            }

            NoOfFillerList = new ObservableCollection<int>();
            for (int i = 0; i <= 3; i++)
            {
                NoOfFillerList.Add(i);
            }


            //string colorExcelFilePath = ConfigurationManager.AppSettings["colorExcel"];
            string colorExcelFilePath = "Resorces\\ColorData.xlsx";
            LoadColorList(colorExcelFilePath);
            LoadMaterialLists(colorExcelFilePath);



            #endregion
        }

        #region Properties
        // Gets the formatted application version string
        public string ApplicationVersion
        {
            get
            {
                string titlePrefix = "Cable Configurator_";
                var version = System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.ToString();
                return $"{titlePrefix} V{version}";
            }
        }

        private ProjectDetails _projectDetails;
        public ProjectDetails ProjectDetails
        {
            get => _projectDetails;
            set
            {
                // Unsubscribe from previous parameters
                if (_projectDetails?.parameters != null)
                    _projectDetails.parameters.PropertyChanged -= OnParametersValidationChanged;

                _projectDetails = value;
                OnPropertyChanged(nameof(ProjectDetails));

                // Subscribe to new parameters' validation changes
                if (_projectDetails?.parameters != null)
                    _projectDetails.parameters.PropertyChanged += OnParametersValidationChanged;
            }
        }

        private string _projectRootPath;
        public string ProjectRootPath
        {
            get { return _projectRootPath; }
            set { _projectRootPath = value; }
        }

        private Visibility _lodingWheelVisibility = Visibility.Hidden;
        public Visibility LodingWheelVisibility
        {
            get => _lodingWheelVisibility;
            set
            {
                _lodingWheelVisibility = value;
                OnPropertyChanged(nameof(LodingWheelVisibility));
            }
        }

        #endregion

        // Event and method for property change notifications
        public event PropertyChangedEventHandler PropertyChanged;
        internal virtual void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        // When CableParameters.HasErrors changes, notify the command
        private void OnParametersValidationChanged(object sender, PropertyChangedEventArgs e)
        {
            if (e.PropertyName == nameof(CableParameters.HasErrors))
            {
                GenerateCommand.RaiseCanExecuteChanged();
            }
        }


        //private methods
        private string GetProjectRootPathFromConfig()
        {
            string projectRootPathFinal = string.Empty;
            // Retrieve from App.config
            string projectRootPath = ConfigurationManager.AppSettings["ProjectRootPath"];

            // Check if ServerRootPath is not empty or null
            if (!string.IsNullOrEmpty(projectRootPath))
            {
                // Use the retrieved ServerRootPath value
                projectRootPathFinal = projectRootPath;
                // Create the directory if it doesn't exist
                if (!Directory.Exists(projectRootPathFinal))
                {
                    Directory.CreateDirectory(projectRootPathFinal);
                }
            }
            else
            {
                // Provide a default value if ServerRootPath is not found in App.config
                projectRootPathFinal = @"C:\Temp\CableConfigurator";
                // Create the directory if it doesn't exist
                if (!Directory.Exists(projectRootPathFinal))
                {
                    Directory.CreateDirectory(projectRootPathFinal);
                }

            }
            return projectRootPathFinal;
        }

        //update status
        private string _statusMessage = "Ready";  // Default message or initialize in constructor

        public string StatusMessage
        {
            get { return _statusMessage; }
            set
            {
                if (_statusMessage != value)
                {
                    _statusMessage = value;
                    OnPropertyChanged(nameof(StatusMessage));  // Notify the UI of property change
                }
            }
        }

        //UI cable data enable props
        private bool _cableInfoPanelEnabled;
        public bool CableInfoPanelEnabled
        {
            get { return _cableInfoPanelEnabled; }
            set
            {
                if (_cableInfoPanelEnabled != value)
                {
                    _cableInfoPanelEnabled = value;
                    OnPropertyChanged(nameof(CableInfoPanelEnabled));  // Notify the UI of property change
                }
            }
        }

        private bool _isInsulationEnabled;
        public bool IsInsulationEnabled
        {
            get { return _isInsulationEnabled; }
            set
            {
                if (_isInsulationEnabled != value)
                {
                    _isInsulationEnabled = value;
                    OnPropertyChanged(nameof(IsInsulationEnabled));  // Notify the UI of property change
                                                                     // Clear the related data when insulation is not enabled
                    if (!_isInsulationEnabled)
                    {
                        ProjectDetails.parameters.spacing_2 = 0;
                        ProjectDetails.parameters.insulationMaterial = null;
                    }
                }
            }
        }

        private bool _isConductorScreenEnabled;
        public bool IsConductorScreenEnabled
        {
            get { return _isConductorScreenEnabled; }
            set
            {
                if (_isConductorScreenEnabled != value)
                {
                    _isConductorScreenEnabled = value;
                    OnPropertyChanged(nameof(IsConductorScreenEnabled));  // Notify the UI of property change                                 
                    if (!_isConductorScreenEnabled)
                    {
                        SelectedNumberOfLayers = 0;
                        ProjectDetails.parameters.spacing_3 = 0;
                        ProjectDetails.parameters.layer_1Material = null;
                        ProjectDetails.parameters.spacing_4 = 0;
                        ProjectDetails.parameters.layer_2Material = null;
                        ProjectDetails.parameters.spacing_5 = 0;
                        ProjectDetails.parameters.layer_3Material = null;
                    }
                }
            }
        }

        private bool _isFillerEnable;
        public bool IsFillerEnable
        {
            get { return _isFillerEnable; }
            set
            {
                if (_isFillerEnable != value)
                {
                    _isFillerEnable = value;
                    OnPropertyChanged(nameof(IsFillerEnable));  // Notify the UI of property change
                    ProjectDetails.parameters.fillerchoice = 1;

                    if (!_isFillerEnable)
                    {
                        ProjectDetails.parameters.FillingMethod = null;
                        ProjectDetails.parameters.SelectedNumberOfFillers = 0;
                        ProjectDetails.parameters.Filler1 = 0;
                        ProjectDetails.parameters.Filler2 = 0;
                        ProjectDetails.parameters.Filler3 = 0;
                        ProjectDetails.parameters.fillerchoice = 0;
                        ProjectDetails.parameters.FillerMaterial = null;

                    }
                }
            }
        }

        private int _selectedNumberOfLayers;
        public int SelectedNumberOfLayers
        {
            get => _selectedNumberOfLayers;
            set
            {
                _selectedNumberOfLayers = value;
                OnPropertyChanged(nameof(SelectedNumberOfLayers));
            }
        }

        private bool _isInsulationScreenEnable;
        public bool IsInsulationScreenEnable
        {
            get { return _isInsulationScreenEnable; }
            set
            {
                if (_isInsulationScreenEnable != value)
                {
                    _isInsulationScreenEnable = value;
                    OnPropertyChanged(nameof(IsInsulationScreenEnable));  // Notify the UI of property change

                    if (!_isInsulationScreenEnable)
                    {
                        ProjectDetails.parameters.preinnersheaththickness = 0;
                        ProjectDetails.parameters.insulationScreenMaterial = null;
                        ProjectDetails.parameters.preinnersheathcolor = null;

                    }
                }
            }
        }

        private bool _isInnerSheathEnable;
        public bool IsInnerSheathEnable
        {
            get { return _isInnerSheathEnable; }
            set
            {
                if (_isInnerSheathEnable != value)
                {
                    _isInnerSheathEnable = value;
                    OnPropertyChanged(nameof(IsInnerSheathEnable));  // Notify the UI of property change

                    if (!_isInnerSheathEnable)
                    {
                        ProjectDetails.parameters.innersheaththickness = 0;
                        ProjectDetails.parameters.innerSheathMaterial = null;
                        ProjectDetails.parameters.innersheathcolor = null;
                        ProjectDetails.parameters.overinnersheaththickness = 0;
                        ProjectDetails.parameters.overinnersheathcolor = null;
                        IsoverinnersheaththicknessEnable = false;
                    }
                }
            }
        }

        private bool _isArmoringEnable;
        public bool IsArmoringEnable
        {
            get { return _isArmoringEnable; }
            set
            {
                if (_isArmoringEnable != value)
                {
                    _isArmoringEnable = value;
                    OnPropertyChanged(nameof(IsArmoringEnable));  // Notify the UI of property change

                    if (!_isInnerSheathEnable)
                    {

                        ProjectDetails.parameters.armor_choice = null;
                        ProjectDetails.parameters.cylinder_dia = 0;
                        ProjectDetails.parameters.side_length = 0;
                        ProjectDetails.parameters.side_thickness = 0;
                        ProjectDetails.parameters.armorcolor = null;
                    }
                }
            }
        }

        private bool _isOuterSheathEnable;
        public bool IsOuterSheathEnable
        {
            get { return _isOuterSheathEnable; }
            set
            {
                if (_isOuterSheathEnable != value)
                {
                    _isOuterSheathEnable = value;
                    OnPropertyChanged(nameof(IsOuterSheathEnable));  // Notify the UI of property change

                    if (!_isOuterSheathEnable)
                    {
                        ProjectDetails.parameters.outersheaththickness = 0;
                        ProjectDetails.parameters.outersheathcolor = null;
                        ProjectDetails.parameters.outersheathLineRequired = false;
                        ProjectDetails.parameters.outercolor2 = null;
                        ProjectDetails.parameters.outerSheathMaterial = null;
                    }
                }
            }
        }

        private bool _isTapingEnabled;
        public bool IsTapingEnabled
        {
            get { return _isTapingEnabled; }
            set
            {
                if (_isTapingEnabled != value)
                {
                    _isTapingEnabled = value;
                    OnPropertyChanged(nameof(IsTapingEnabled));  // Notify the UI of property change

                    if (!_isTapingEnabled)
                    {
                        ProjectDetails.parameters.armortapingthickness = 0;
                    }
                }
            }
        }

        private bool _isoverinnersheaththicknessEnable;
        public bool IsoverinnersheaththicknessEnable
        {
            get { return _isoverinnersheaththicknessEnable; }
            set
            {
                if (_isoverinnersheaththicknessEnable != value)
                {
                    _isoverinnersheaththicknessEnable = value;
                    OnPropertyChanged(nameof(IsoverinnersheaththicknessEnable));  // Notify the UI of property change

                    if (!_isoverinnersheaththicknessEnable)
                    {
                        ProjectDetails.parameters.overinnersheaththickness = 0;
                    }
                }
            }
        }

        private string _selectedCableCoreType;
        public string SelectedCableCoreType
        {
            get => _selectedCableCoreType;
            set
            {
                if (_selectedCableCoreType != value)
                {
                    ProjectDetails.cableCoreType = value;

                    _selectedCableCoreType = value;
                    OnPropertyChanged(nameof(SelectedCableCoreType));
                    UpdateNoOfLayersBasedOnCoreType();
                    UpdateWindowHeight();
                }
            }
        }

        private void UpdateNoOfLayersBasedOnCoreType()
        {
            NoOfLayersList.Clear();

            switch (_selectedCableCoreType)
            {
                case "Circular":
                    for (int i = 1; i <= 3; i++)
                        NoOfLayersList.Add(i);
                    SelectedNumberOfLayers = 0;

                    break;
                case "Shaped":
                    NoOfLayersList.Add(1);
                    SelectedNumberOfLayers = 0;

                    break;
                default:
                    NoOfLayersList.Add(0); // Default case to handle undefined core types
                    break;
            }
        }

        private int _windowHeight = 790; // Default height
        public int WindowHeight
        {
            get { return _windowHeight; }
            set
            {
                if (_windowHeight != value) // Check if the value is actually changing
                {
                    _windowHeight = value;
                    OnPropertyChanged(nameof(WindowHeight)); // Notify only on change
                }
            }
        }




        private void UpdateWindowHeight()
        {
            // Set height based on CoreType
            WindowHeight = (SelectedCableCoreType == "Shaped") ? 655 : 790;
        }

        public void LoadColorList(string filePath)
        {
            // Clear existing items
            ColorList.Clear();

            // Get the dictionary from your existing static method
            ColorData = ExcelHelper.ReadColorDataFromExcel(filePath);

            // Populate the ObservableCollection with color names
            foreach (var colorName in ColorData.Keys)
            {
                ColorList.Add(colorName);
            }
        }

        public void LoadMaterialLists(string filePath)
        {
            // Clear existing items
            ConductorMaterialList?.Clear();
            InsulationMaterialList?.Clear();
            ConductorScreenMaterialList?.Clear();
            FillerMaterialList?.Clear();
            InsulationScreenMaterialList?.Clear();
            InnerSheathMaterialList?.Clear();
            OuterSheathMaterialList?.Clear();

            ConductorMaterialList = ExcelHelper.ReadSingleColumnSheet(filePath, "ConductorMaterial");
            InsulationMaterialList = ExcelHelper.ReadSingleColumnSheet(filePath, "InsulationMaterial");
            ConductorScreenMaterialList = ExcelHelper.ReadSingleColumnSheet(filePath, "ConductorScreenMaterial");
            FillerMaterialList = ExcelHelper.ReadSingleColumnSheet(filePath, "FillerMaterial");
            InsulationScreenMaterialList = ExcelHelper.ReadSingleColumnSheet(filePath, "InsulationScreenMaterial");
            InnerSheathMaterialList = ExcelHelper.ReadSingleColumnSheet(filePath, "InnerSheathMaterial");
            OuterSheathMaterialList = ExcelHelper.ReadSingleColumnSheet(filePath, "OuterSheathMaterial");
        }
    }
}