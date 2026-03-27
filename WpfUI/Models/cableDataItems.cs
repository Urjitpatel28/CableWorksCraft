using System.Collections;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using DocumentFormat.OpenXml.Wordprocessing;
using WpfUI.ViewModels;

namespace WpfUI.Models
{
    public class CableParameters : INotifyPropertyChanged, INotifyDataErrorInfo
    {
        private readonly Dictionary<string, List<string>> _errors = new Dictionary<string, List<string>>();

        // Backing fields
        private double _height = 50;
        private int _numConcentricCylinders = 7;
        private double _conductorDia;
        private double _spacing1;
        private double _spacing2;
        private double _spacing3;
        private double _spacing4;
        private double _spacing5;
        private double _spacing6;
        private double _spacing7;
        private double _wireDia;
        private double _wireRadius;
        private double[] _numCylindersPerLayer;
        private double _numCylindersPerLayerSingle = 1;

        //color
        private string _conductorScreenColor;
        private string _insulationColor;
        private string _nometallicScreenColor;
        private string _metallicScreenColor;
        private string _idTapeColor;
        private string _lappingColor;
        private string _wireColor;
        private string _preinnersheathcolor;
        private string _innersheathcolor;
        private string _overinnersheathcolor;
        private string _armorcolor = "Gray";
        private string _armortapingcolor;
        private string _outersheathcolor;
        private string _outercolor1;
        private bool _outersheathLineRequired;
        private string _outerSheathLineColor;
        private string _color1;
        private string _color2;
        private string _color3;
        private string _color4;
        private string _color5;
        private string _halfcondscreencolor;


        private double _halfcore_dia;
        private double _halfcore_radius;
        private double _preinnersheaththickness;
        private double _innersheaththickness;
        private double _overinnersheaththickness;
        private double _cylinder_dia;
        private double _cylinder_radius;
        private double _side_length;
        private double _side_thickness;
        private double _armortapingthickness;
        private double _outersheathThickness;


        private double _armorSize;

        private string _insulationMaterial;
        private string _fillingMethod;
        private int _fillerchoice;

        private int _selectedNumberOfFillers;
        private double _filler1;
        private double _filler2;
        private double _filler3;
        private string _fillerMaterial;
        private double _leftoverDia;

        private string _insulationScreenMaterial;
        private string _innerSheathMaterial;
        private string _outerSheathMaterial;
        private string _printingMatter;

        //for sectoral
        private double _conductorRadius;
        private double _full_radius;
        private double _offset_radius1;
        private double _offset_radius2;
        private double _fillet_radius = 1;
        private double _layyd_dia;



        // Validation logic for double properties
        private void ValidatePositive(string propertyName, double value)
        {
            _errors.Remove(propertyName);

            if (value < 0)
                _errors[propertyName] = new List<string> { $"* This value must be greater than 0" };

            ErrorsChanged?.Invoke(this, new DataErrorsChangedEventArgs(propertyName));
            OnPropertyChanged(nameof(HasErrors)); // Notify HasErrors changed

        }

        public void NotifyValidationStateChanged()
        {
            OnPropertyChanged(nameof(HasErrors)); // Force CanExecute to recheck
        }

        // Example for height property (apply same pattern to all double properties)
        public double height
        {
            get => _height;
            set
            {
                _height = value;
                OnPropertyChanged(nameof(height));
                ValidatePositive(nameof(height), value);

            }
        }

        // Apply the same validation pattern to ALL double properties:

        public double ConductorDia
        {
            get => _conductorDia;
            set
            {
                _conductorDia = value;
                OnPropertyChanged(nameof(ConductorDia));
                ValidatePositive(nameof(ConductorDia), value);
                spacing_1 = _conductorDia / 2;

            }
        }

        public double spacing_1
        {
            get => _spacing1;
            set
            {
                _spacing1 = value;
                OnPropertyChanged(nameof(spacing_1));
                OnPropertyChanged(nameof(offset_radius1));
                OnPropertyChanged(nameof(offset_radius2));
                OnPropertyChanged(nameof(conductor_radius));
                NotifyDependentPropertiesChanged();

                ValidatePositive(nameof(spacing_1), value);
                NotifyValidationStateChanged();
            }
        }

        public double spacing_2
        {
            get => _spacing2;
            set
            {
                _spacing2 = value;
                OnPropertyChanged(nameof(spacing_2));

                OnPropertyChanged(nameof(offset_radius1));
                OnPropertyChanged(nameof(offset_radius2));
                OnPropertyChanged(nameof(conductor_radius));
                NotifyDependentPropertiesChanged();

                ValidatePositive(nameof(spacing_2), value);
                NotifyValidationStateChanged();

                UpdateSpacing1FromLayyd();
            }
        }

        public double spacing_3
        {
            get => _spacing3;
            set
            {
                _spacing3 = value;
                OnPropertyChanged(nameof(spacing_3));

                OnPropertyChanged(nameof(offset_radius1));
                OnPropertyChanged(nameof(offset_radius2));
                OnPropertyChanged(nameof(conductor_radius));
                NotifyDependentPropertiesChanged();

                ValidatePositive(nameof(spacing_3), value);
                NotifyValidationStateChanged();

                UpdateSpacing1FromLayyd();
            }
        }

        public double spacing_4
        {
            get => _spacing4;
            set
            {
                _spacing4 = value;
                OnPropertyChanged(nameof(spacing_4));
                ValidatePositive(nameof(spacing_4), value);
                NotifyValidationStateChanged();

            }
        }

        public double spacing_5
        {
            get => _spacing5;
            set
            {
                _spacing5 = value;
                OnPropertyChanged(nameof(spacing_5));
                ValidatePositive(nameof(spacing_5), value);
            }
        }

        public double spacing_6
        {
            get => _spacing6;
            set
            {
                _spacing6 = value;
                OnPropertyChanged(nameof(spacing_6));
                ValidatePositive(nameof(spacing_6), value);
            }
        }

        public double spacing_7
        {
            get => _spacing7;
            set
            {
                _spacing7 = value;
                OnPropertyChanged(nameof(spacing_7));
                ValidatePositive(nameof(spacing_7), value);
            }
        }

        public double wire_dia
        {
            get => _wireDia;
            set
            {
                _wireDia = value;
                OnPropertyChanged(nameof(wire_dia));
                ValidatePositive(nameof(wire_dia), value);
                NotifyValidationStateChanged();
                wire_radius = _wireDia / 2;

            }
        }

        public double wire_radius
        {
            get => _wireRadius;
            set
            {
                _wireRadius = value;
                OnPropertyChanged(nameof(wire_radius));
                ValidatePositive(nameof(wire_radius), value);
                NotifyValidationStateChanged();

            }
        }

        public double innersheaththickness
        {
            get => _innersheaththickness;
            set
            {
                _innersheaththickness = value;
                OnPropertyChanged(nameof(innersheaththickness));
                ValidatePositive(nameof(innersheaththickness), value);
                NotifyValidationStateChanged();

            }
        }

        public double outersheaththickness
        {
            get => _outersheathThickness;
            set
            {
                _outersheathThickness = value;
                OnPropertyChanged(nameof(outersheaththickness));
                ValidatePositive(nameof(outersheaththickness), value);
                NotifyValidationStateChanged();

            }
        }

        public double armor_Size
        {
            get => _armorSize;
            set
            {
                _armorSize = value;
                OnPropertyChanged(nameof(armor_Size));
                ValidatePositive(nameof(armor_Size), value);
                NotifyValidationStateChanged();
                if (armor_choice == "1")
                {
                    cylinder_radius = _armorSize;
                }

                if (armor_choice == "2")
                {
                    side_length = _armorSize;
                }

            }
        }

        public double cylinder_dia
        {
            get => _cylinder_dia;
            set
            {
                _cylinder_dia = value;
                OnPropertyChanged(nameof(cylinder_dia));
                ValidatePositive(nameof(cylinder_dia), value);
                NotifyValidationStateChanged();

                cylinder_radius = _cylinder_dia / 2;

            }
        }


        public double cylinder_radius
        {
            get => _cylinder_radius;
            set
            {
                _cylinder_radius = value;
                OnPropertyChanged(nameof(cylinder_radius));
                ValidatePositive(nameof(cylinder_radius), value);
                NotifyValidationStateChanged();

            }
        }

        public double side_length
        {
            get => _side_length;
            set
            {
                _side_length = value;
                OnPropertyChanged(nameof(side_length));
                ValidatePositive(nameof(side_length), value);
                NotifyValidationStateChanged();
            }
        }

        public double side_thickness
        {
            get => _side_thickness;
            set
            {
                _side_thickness = value;
                OnPropertyChanged(nameof(side_thickness));
                ValidatePositive(nameof(side_thickness), value);
                NotifyValidationStateChanged();
            }
        }

        public int num_concentric_cylinders
        {
            get => _numConcentricCylinders;
            set
            {
                _numConcentricCylinders = value;
                OnPropertyChanged(nameof(num_concentric_cylinders));

            }
        }

        public double numCylindersPerLayer
        {
            get => _numCylindersPerLayerSingle;
            set
            {
                _numCylindersPerLayerSingle = value;
                OnPropertyChanged(nameof(numCylindersPerLayer));

                // Reset the halfcore_radius if the new value is not a decimal
                if (value % 1 == 0)
                {
                    halfcore_radius = 0;
                }

            }
        }

        public double[] num_cylinders_per_layer
        {
            get => _numCylindersPerLayer;
            set
            {
                _numCylindersPerLayer = value;
                OnPropertyChanged(nameof(num_cylinders_per_layer));

            }
        }

        private string _armorChoice;
        public string armor_choice
        {
            get => _armorChoice;
            set
            {
                string valueToSet = ConvertSelectionToValue(value);
                if (_armorChoice != valueToSet)
                {
                    _armorChoice = valueToSet;
                    OnPropertyChanged(nameof(armor_choice));
                    if (_armorChoice == "1")
                    {
                        IsCubicalArmor = false;
                        IsWireArmor = true;
                        side_length = 0;
                        side_thickness = 0;
                    }
                    if (_armorChoice == "2")
                    {
                        IsCubicalArmor = true;
                        IsWireArmor = false;
                        cylinder_dia = 0;
                    }
                }
            }
        }



        public string insulationScreenMaterial
        {
            get => _insulationScreenMaterial;
            set
            {
                _insulationScreenMaterial = value;
                OnPropertyChanged(nameof(insulationScreenMaterial));
            }
        }

        public string innerSheathMaterial
        {
            get => _innerSheathMaterial;
            set
            {
                _innerSheathMaterial = value;
                OnPropertyChanged(nameof(innerSheathMaterial));
            }
        }

        public string outerSheathMaterial
        {
            get => _outerSheathMaterial;
            set
            {
                _outerSheathMaterial = value;
                OnPropertyChanged(nameof(outerSheathMaterial));
            }
        }

        //colors
        public string conductorScreenColor
        {
            get => _conductorScreenColor;
            set
            {
                _conductorScreenColor = value;
                OnPropertyChanged(nameof(conductorScreenColor));
            }
        }

        public string insulationColor
        {
            get => _insulationColor;
            set
            {
                _insulationColor = value;
                OnPropertyChanged(nameof(insulationColor));
            }
        }

        public string nometallicScreenColor
        {
            get => _nometallicScreenColor;
            set
            {
                _nometallicScreenColor = value;
                OnPropertyChanged(nameof(nometallicScreenColor));
            }
        }

        public string metallicScreenColor
        {
            get => _metallicScreenColor;
            set
            {
                _metallicScreenColor = value;
                OnPropertyChanged(nameof(metallicScreenColor));
            }
        }

        public string idTapeColor
        {
            get => _idTapeColor;
            set
            {
                _idTapeColor = value;
                OnPropertyChanged(nameof(idTapeColor));
            }
        }

        public string lappingColor
        {
            get => _lappingColor;
            set
            {
                _lappingColor = value;
                OnPropertyChanged(nameof(lappingColor));
            }
        }

        public string wireColor
        {
            get => _wireColor;
            set
            {
                _wireColor = value;
                OnPropertyChanged(nameof(wireColor));
            }
        }

        public string preinnersheathcolor
        {
            get => _preinnersheathcolor;
            set
            {
                _preinnersheathcolor = value;
                OnPropertyChanged(nameof(preinnersheathcolor));
            }
        }

        public string innersheathcolor
        {
            get => _innersheathcolor;
            set
            {
                _innersheathcolor = value;
                OnPropertyChanged(nameof(innersheathcolor));
            }
        }

        public string overinnersheathcolor
        {
            get => _overinnersheathcolor;
            set
            {
                _overinnersheathcolor = value;
                OnPropertyChanged(nameof(overinnersheathcolor));
            }
        }

        public string armorcolor
        {
            get => _armorcolor;
            set
            {
                _armorcolor = value;
                OnPropertyChanged(nameof(armorcolor));
            }
        }

        public string armortapingcolor
        {
            get => _armortapingcolor;
            set
            {
                _armortapingcolor = value;
                OnPropertyChanged(nameof(armortapingcolor));
            }
        }

        public string outersheathcolor
        {
            get => _outersheathcolor;
            set
            {
                _outersheathcolor = value;
                OnPropertyChanged(nameof(outersheathcolor));
                OnPropertyChanged(nameof(printingMatterColor));

                // Reflect to outercolor2 if needed
                if (outercolorchoice == 2)
                {
                    outercolor2 = value;
                }
                else
                {
                    outercolor2 = null;
                }
            }
        }

        public bool outersheathLineRequired
        {
            get => _outersheathLineRequired;
            set
            {
                if (_outersheathLineRequired != value)
                {
                    _outersheathLineRequired = value;
                    OnPropertyChanged(nameof(outersheathLineRequired));
                    OnPropertyChanged(nameof(outercolorchoice));
                    UpdateOuterColor1();

                    if (!value)
                    {
                        outercolor2 = null;
                    }
                }
            }
        }

        public string outercolor1
        {
            get => _outercolor1;
            set
            {
                if (_outercolor1 != value)
                {
                    _outercolor1 = value;
                    OnPropertyChanged(nameof(outercolor1));
                }
            }
        }

        private void UpdateOuterColor1()
        {
            outercolor2 = outercolorchoice == 2 ? outersheathcolor : null;
        }

        public int outercolorchoice => outersheathLineRequired ? 2 : 1;

        public string outercolor2
        {
            get => _outerSheathLineColor;
            set
            {
                _outerSheathLineColor = value;
                OnPropertyChanged(nameof(outercolor2));
            }
        }

        public string condscreencolor1
        {
            get => _color1;
            set
            {
                _color1 = value;
                OnPropertyChanged(nameof(condscreencolor1));
            }
        }

        public string condscreencolor2
        {
            get => _color2;
            set
            {
                _color2 = value;
                OnPropertyChanged(nameof(condscreencolor2));
            }
        }

        public string condscreencolor3
        {
            get => _color3;
            set
            {
                _color3 = value;
                OnPropertyChanged(nameof(condscreencolor3));
            }
        }

        public string condscreencolor4
        {
            get => _color4;
            set
            {
                _color4 = value;
                OnPropertyChanged(nameof(condscreencolor4));
            }
        }

        public string condscreencolor5
        {
            get => _color5;
            set
            {
                _color5 = value;
                OnPropertyChanged(nameof(condscreencolor5));
            }
        }
        public string halfcondscreencolor
        {
            get => _halfcondscreencolor;
            set
            {
                _halfcondscreencolor = value;
                OnPropertyChanged(nameof(halfcondscreencolor));
            }
        }

        public string fraccondscreencolor => halfcondscreencolor;

        public string printingMatterColor
        {
            get
            {
                return string.Equals(outersheathcolor, "black", StringComparison.OrdinalIgnoreCase)
                    ? "(1,1,1)"
                    : "(0,0,0)";
            }
        }

        private string ConvertSelectionToValue(string selection)
        {
            switch (selection)
            {
                case "Wire":
                    return "1";
                case "Strip":
                    return "2";
                default:
                    return null;  // Or however you wish to handle unspecified or incorrect selections
            }
        }


        public int fillerchoice
        {
            get => _fillerchoice;
            set
            {
                _fillerchoice = value;
                OnPropertyChanged(nameof(fillerchoice));
            }
        }

        public string FillingMethod
        {
            get => _fillingMethod;
            set
            {
                if (_fillingMethod != value)
                {
                    _fillingMethod = value;
                    OnPropertyChanged(nameof(FillingMethod));
                    if (_fillingMethod == "Auto")
                    {
                        SelectedNumberOfFillers = 0;
                        Filler1 = 0;
                        Filler2 = 0;
                        Filler3 = 0;
                    }
                }
            }
        }

        public int SelectedNumberOfFillers
        {
            get => _selectedNumberOfFillers;
            set
            {
                if (_selectedNumberOfFillers != value)
                {
                    _selectedNumberOfFillers = value;
                    OnPropertyChanged(nameof(SelectedNumberOfFillers));

                    // Reset fillers when not applicable
                    Filler1 = _selectedNumberOfFillers >= 1 ? Filler1 : 0;
                    Filler2 = _selectedNumberOfFillers >= 2 ? Filler2 : 0;
                    Filler3 = _selectedNumberOfFillers >= 3 ? Filler3 : 0;
                }
            }
        }


        public double Filler1
        {
            get => _filler1;
            set
            {
                _filler1 = value;
                OnPropertyChanged(nameof(Filler1));
                //OnPropertyChanged(nameof(fillerDiameters));
            }
        }

        public double Filler2
        {
            get => _filler2;
            set
            {
                _filler2 = value;
                OnPropertyChanged(nameof(Filler2));
                //OnPropertyChanged(nameof(fillerDiameters));
            }
        }

        public double Filler3
        {
            get => _filler3;
            set
            {
                _filler3 = value;
                OnPropertyChanged(nameof(Filler3));
                //OnPropertyChanged(nameof(fillerDiameters));
            }
        }

        public List<double> fillerDiameters
        {
            get
            {
                return new List<double> { Filler1, Filler2, Filler3 }.Where(x => x != 0).ToList();
            }
        }

        // ShouldSerialize method to conditionally serialize FillerDiameters
        public bool ShouldSerializeFillerDiameters()
        {
            return FillingMethod != "Auto";
        }

        public string FillerMaterial
        {
            get => _fillerMaterial;
            set
            {
                _fillerMaterial = value;
                OnPropertyChanged(nameof(FillerMaterial));
            }
        }

        public double leftoverDia
        {
            get => _leftoverDia;
            set
            {
                _leftoverDia = value;
                OnPropertyChanged(nameof(leftoverDia));
            }
        }

        public double preinnersheaththickness
        {
            get => _preinnersheaththickness;
            set
            {
                _preinnersheaththickness = value;
                OnPropertyChanged(nameof(preinnersheaththickness));
            }
        }

        public double overinnersheaththickness
        {
            get => _overinnersheaththickness;
            set
            {
                _overinnersheaththickness = value;
                OnPropertyChanged(nameof(overinnersheaththickness));
            }
        }

        public double armortapingthickness
        {
            get => _armortapingthickness;
            set
            {
                _armortapingthickness = value;
                OnPropertyChanged(nameof(armortapingthickness));
            }
        }

        public double halfcore_dia
        {
            get => _halfcore_dia;
            set
            {
                if (_halfcore_dia != value)
                {
                    _halfcore_dia = value;
                    OnPropertyChanged(nameof(halfcore_dia));
                }
            }
        }

        public double halfcore_radius
        {
            get => _halfcore_dia / 2;
            set => halfcore_dia = value * 2;
        }


        //materials
        private string _conductorMaterial;
        public string conductorMaterial
        {
            get => _conductorMaterial;
            set
            {
                if (_conductorMaterial != value)
                {
                    _conductorMaterial = value;
                    OnPropertyChanged(nameof(conductorMaterial));
                }
            }
        }


        public string insulationMaterial
        {
            get => _insulationMaterial;
            set
            {
                if (_insulationMaterial != value)
                {
                    _insulationMaterial = value;
                    OnPropertyChanged(nameof(insulationMaterial));
                }
            }
        }


        private string _layer_1Material;
        public string layer_1Material
        {
            get => _layer_1Material;
            set
            {
                if (_layer_1Material != value)
                {
                    _layer_1Material = value;
                    OnPropertyChanged(nameof(layer_1Material));
                }
            }
        }

        private string _layer_2Material;
        public string layer_2Material
        {
            get => _layer_2Material;
            set
            {
                if (_layer_2Material != value)
                {
                    _layer_2Material = value;
                    OnPropertyChanged(nameof(layer_2Material));
                }
            }
        }

        private string _layer_3Material;
        public string layer_3Material
        {
            get => _layer_3Material;
            set
            {
                if (_layer_3Material != value)
                {
                    _layer_3Material = value;
                    OnPropertyChanged(nameof(layer_3Material));
                }
            }
        }

        public string printingMatter
        {
            get => _printingMatter;
            set
            {
                if (_printingMatter != value)
                {
                    _printingMatter = value;
                    OnPropertyChanged(nameof(printingMatter));
                }
            }
        }




        // INotifyDataErrorInfo implementation
        public event EventHandler<DataErrorsChangedEventArgs> ErrorsChanged;
        public bool HasErrors => _errors.Any();

        public IEnumerable GetErrors(string propertyName)
        {
            if (string.IsNullOrEmpty(propertyName) || !_errors.ContainsKey(propertyName))
                return Enumerable.Empty<string>();

            return _errors[propertyName];
        }

        // INotifyPropertyChanged
        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged(string propertyName) =>
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));



        private void NotifyDependentPropertiesChanged()
        {
            OnPropertyChanged(nameof(spacing_1));
            OnPropertyChanged(nameof(spacing_2));
            OnPropertyChanged(nameof(spacing_3));
        }


        private bool _isWireArmor;
        public bool IsWireArmor
        {
            get { return _isWireArmor; }
            set
            {
                if (_isWireArmor != value)
                {
                    _isWireArmor = value;
                    OnPropertyChanged(nameof(IsWireArmor));  // Notify the UI of property change

                    if (!_isWireArmor)
                    {
                        cylinder_dia = 0;
                    }
                }
            }
        }

        private bool _isCubeArmor;
        public bool IsCubicalArmor
        {
            get { return _isCubeArmor; }
            set
            {
                if (_isCubeArmor != value)
                {
                    _isCubeArmor = value;
                    OnPropertyChanged(nameof(IsCubicalArmor));  // Notify the UI of property change

                    if (!_isCubeArmor)
                    {
                        side_length = 0;
                        side_thickness = 0;
                    }
                }
            }
        }

        //for sectoral
        public double offset_radius1 => spacing_1;
        public double offset_radius2 => spacing_1 + spacing_2;
        public double conductor_radius => spacing_1 + spacing_2 + spacing_3;
        public double full_radius => conductor_radius;


        public double fillet_radius
        {
            get => _fillet_radius;
            set
            {
                _fillet_radius = value;
                OnPropertyChanged(nameof(fillet_radius));
            }
        }

        public double layyd_dia
        {
            get => _layyd_dia;
            set
            {
                _layyd_dia = value;
                OnPropertyChanged(nameof(layyd_dia));  
                UpdateSpacing1FromLayyd();              
            }
        }

        public double layyd_rad => layyd_dia / 2.0;

        private void UpdateSpacing1FromLayyd()
        {
            if (layyd_rad > 0)
            {
                spacing_1 = layyd_rad - spacing_2 - spacing_3;
            }
        }

        public int Outerstripangle = 160;
        public int oangle = 160;
    }
}