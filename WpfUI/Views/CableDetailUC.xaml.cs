using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace WpfUI.Views
{
    /// <summary>
    /// Interaction logic for CableDetailUC.xaml
    /// </summary>
    public partial class CableDetailUC : UserControl
    {
        public CableDetailUC()
        {
            InitializeComponent();
        }

        private void ConductorScreenCheckBox_Unchecked(object sender, RoutedEventArgs e)
        {
            ColorLayer1.SelectedIndex = -1;
            ColorLayer2.SelectedIndex = -1;
            ColorLayer3.SelectedIndex = -1;
        }

        private void ClearUnusedColors(int numLayers)
        {
            if (numLayers < 5 && Color5ComboBox != null)
                Color5ComboBox.SelectedIndex = -1;

            if (numLayers < 4 && Color4ComboBox != null)
                Color4ComboBox.SelectedIndex = -1;

            if (numLayers < 3 && Color3ComboBox != null)
                Color3ComboBox.SelectedIndex = -1;

            if (numLayers < 2 && Color2ComboBox != null)
                Color2ComboBox.SelectedIndex = -1;

            if (numLayers < 1 && Color1ComboBox != null)
                Color1ComboBox.SelectedIndex = -1;
            if (numLayers > 5)
            {
                Color1ComboBox.SelectedIndex = -1;
                Color2ComboBox.SelectedIndex = -1;
                Color3ComboBox.SelectedIndex = -1;
                Color4ComboBox.SelectedIndex = -1;
                Color5ComboBox.SelectedIndex = -1;
                Color6ComboBox.SelectedIndex = -1;
            }
        }

        private void NumLayersComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (int.TryParse(NoOfCoreComboBox.Text, out int selectedLayerCount))
            {
                ClearUnusedColors(selectedLayerCount);
            }
        }

        private void NumLayersComboBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (int.TryParse(NoOfCoreSectoralComboBox.Text, out int selectedLayerCount))
            {
                ClearUnusedColors(selectedLayerCount);
            }
        }
    }
}
