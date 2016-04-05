Beginning signomial solve.
Solving took 5 GP solves and 0.952 seconds.

Cost
----
 2.035e+09 [N**2] 

Free Variables
--------------
      A_{floor} : 0.01569    [m**2]    Floor beam x-sectional area                 
       A_{fuse} : 10.81      [m**2]    Fuselage x-sectional area                   
       A_{hold} : 1.026      [m**2]    Cargo hold x-sectional area                 
       A_{skin} : 0.01087    [m**2]    Skin cross sectional area                   
              D : 1.35e+04   [N]       Total drag in cruise                        
   D_{friction} : 7988       [N]       Friction drag                               
    D_{upsweep} : 5513       [N]       Drag due to fuse upsweep                    
             FF : 1.076                Fuselage form factor                        
      M_{floor} : 4.442e+05  [N*m]     Max bending moment in floor beams           
      P_{floor} : 1.137e+06  [N]       Distributed floor load                      
            Q_v : 1.005e+05  [N*m]     Torsion moment imparted by tail             
       R_{fuse} : 1.855      [m]       Fuselage radius                             
       S_{bulk} : 21.62      [m**2]    Bulkhead surface area                       
      S_{floor} : 5.686e+05  [N]       Maximum shear in floor beams                
       S_{nose} : 49.82      [m**2]    Nose surface area                           
       V_{bulk} : 0.02016    [m**3]    Bulkhead skin volume                        
      V_{cabin} : 315        [m**3]    Cabin volume                                
      V_{cargo} : 6.796      [m**3]    Cargo volume                                
       V_{cone} : 0.007483   [m**3]    Cone skin volume                            
        V_{cyl} : 0.2653     [m**3]    Cylinder skin volume                        
      V_{floor} : 0.04902    [m**3]    Floor volume                                
       V_{hold} : 25.04      [m**3]    Hold volume                                 
       V_{lugg} : 18.24      [m**3]    Luggage volume                              
       V_{nose} : 0.04645    [m**3]    Nose skin volume                            
        W_{apu} : 5657       [N]       APU weight                                  
       W_{buoy} : 1517       [N]       Buoyancy weight                             
       W_{cone} : 356.7      [N]       Cone weight                                 
      W_{floor} : 6570       [N]       Floor weight                                
       W_{fuse} : 1.507e+05  [N]       Fuselage weight                             
      W_{insul} : 4307       [N]       Insulation material weight                  
       W_{lugg} : 1.79e+04   [N]       Passenger luggage weight                    
       W_{padd} : 6.465e+04  [N]       Misc weights (galley, toilets, doors etc.)  
       W_{pass} : 1.337e+05  [N]       Passenger weight                            
        W_{pay} : 1.616e+05  [N]       Payload weight                              
       W_{seat} : 2.79e+04   [N]       Seating weight                              
      W_{shell} : 1.582e+04  [N]       Shell weight                                
       W_{skin} : 8791       [N]       Skin weight                                 
     W_{window} : 1.062e+04  [N]       Window weight                               
 \lambda_{cone} : 0.4                  Tailcone radius taper ratio (xshell2->xtail)
           \phi : 0.1749               Upsweep angle                               
   \rho_{cabin} : 0.8711     [kg/m**3] Air density in cabin                        
       \sigma_x : 3.831e+07  [N/m**2]  Axial stress in skin                        
\sigma_{\theta} : 1.034e+08  [N/m**2]  Skin hoop stress                            
    \tau_{cone} : 1.034e+08  [N/m**2]  Shear stress in cone                        
              f : 10.68                Fineness ratio                              
      h_{floor} : 0.3712     [m]       Floor I-beam height                         
       h_{hold} : 0.4838     [m]       Height of the cargo hold                    
       l_{cone} : 10         [m]       Cone length                                 
      l_{floor} : 28.12      [m]       Floor length                                
       l_{fuse} : 39.61      [m]       Fuselage length                             
       l_{nose} : 5.2        [m]       Nose length                                 
      l_{shell} : 24.41      [m]       Shell length                                
       n_{pass} : 167                  Number of passengers                        
       n_{rows} : 31                   Number of rows                              
  p_{\lambda_v} : 1.6                  1 + 2*Tail taper ratio                      
       t_{cone} : 4.494e-05  [m]       Cone thickness                              
      t_{shell} : 0.001259   [m]       Shell thickness                             
       t_{skin} : 0.0009324  [m]       Skin thickness                              
      w_{floor} : 3.125      [m]       Floor width                                 
     x_{shell1} : 5.2        [m]       Start of cylinder section                   

Constants
---------
            LF : 0.898                 Load factor                                    
   L_{v_{max}} : 3.5e+04    [N]        Max vertical tail load                         
      N_{land} : 6                     Emergency landing load factor                  
             R : 287        [J/K/kg]   Universal gas constant                         
           SPR : 6                     Number of seats per row                        
     T_{cabin} : 300        [K]        Cabin temperature                              
    V_{\infty} : 234        [m/s]      Cruise velocity                                
   W''_{floor} : 60         [N/m**2]   Floor weight/area density                      
   W''_{insul} : 22         [N/m**2]   Weight/area density of insulation material     
     W'_{seat} : 150        [N]        Weight per seat                                
   W'_{window} : 435        [N/m]      Weight/length density of windows               
 W_{avg. pass} : 180        [lbf]      Average passenger weight                       
     W_{cargo} : 1e+04      [N]        Cargo weight                                   
  W_{carry on} : 15         [lbf]      Ave. carry-on weight                           
   W_{checked} : 40         [lbf]      Ave. checked bag weight                        
       W_{fix} : 3000       [lbf]      Fixed weights (pilots, cockpit seats, navcom)  
      \Delta h : 1          [m]        Distance from floor to widest part of fuselage 
      \Delta p : 5.2e+04    [Pa]       Pressure difference across fuselage skin       
           \mu : 1.4e-05    [N*s/m**2] Dynamic viscosity (35,000ft)                   
 \rho_{\infty} : 0.38       [kg/m**3]  Air density (35,000ft)                         
   \rho_{bend} : 2700       [kg/m**3]  Stringer density                               
  \rho_{cargo} : 150        [kg/m**3]  Cargo density                                  
   \rho_{cone} : 2700       [kg/m**3]  Cone material density                          
  \rho_{floor} : 2700       [kg/m**3]  Floor material density                         
   \rho_{lugg} : 100        [kg/m**3]  Luggage density                                
   \rho_{skin} : 2700       [kg/m**3]  Skin density                                   
\sigma_{floor} : 2.069e+08  [N/m**2]   Max allowable cap stress                       
 \sigma_{skin} : 1.034e+08  [N/m**2]   Max allowable skin stress                      
  \tau_{floor} : 2.069e+08  [N/m**2]   Max allowable shear web stress                 
           b_v : 7          [m]        Vertical tail span                             
        c_{vt} : 4          [m]        Vertical tail chord                            
       f_{apu} : 0.035                 APU weight as fraction of payload weight       
      f_{fadd} : 0.2                   Fractional added weight of local reinforcements
     f_{frame} : 0.25                  Fractional frame weight                        
    f_{lugg,1} : 0.4                   Proportion of passengers with one suitcase     
    f_{lugg,2} : 0.1                   Proportion of passengers with two suitcases    
      f_{padd} : 0.4                   Other misc weight as fraction of payload weight
    f_{string} : 0.35                  Fractional weight of stringers                 
             g : 9.81       [m/s**2]   Gravitational acceleration                     
      n_{seat} : 186                    Number of seats                               
           p_s : 31         [in]       Seat pitch                                     
     p_{cabin} : 7.5e+04    [Pa]       Cabin air pressure (8,000ft)                   
           r_E : 1                     Ratio of stringer/skin moduli                  
     w_{aisle} : 0.51       [m]        Aisle width                                    
      w_{seat} : 0.5        [m]        Seat width                                     
       w_{sys} : 0.1        [m]        Width between cabin and skin for systems       

Sensitivities
-------------
     w_{seat} : 2.23     Seat width                                     
   V_{\infty} : 1.882    Cruise velocity                                
          SPR : 1.771    Number of seats per row                        
     n_{seat} : 1.095     Number of seats                               
\rho_{\infty} : 0.8739   Air density (35,000ft)                         
          p_s : 0.4586   Seat pitch                                     
           LF : 0.4501   Load factor                                    
     f_{padd} : 0.4289   Other misc weight as fraction of payload weight
W_{avg. pass} : 0.392    Average passenger weight                       
    w_{aisle} : 0.3791   Aisle width                                    
    W'_{seat} : 0.1863   Weight per seat                                
      w_{sys} : 0.1487   Width between cabin and skin for systems       
          \mu : 0.1183   Dynamic viscosity (35,000ft)                   
            g : 0.118    Gravitational acceleration                     
  \rho_{skin} : 0.105    Skin density                                   
     \Delta p : 0.105    Pressure difference across fuselage skin       
      W_{fix} : 0.08852  Fixed weights (pilots, cockpit seats, navcom)  
  W'_{window} : 0.07044  Weight/length density of windows               
  W_{checked} : 0.05807  Ave. checked bag weight                        
   f_{lugg,1} : 0.03871  Proportion of passengers with one suitcase     
      f_{apu} : 0.03753  APU weight as fraction of payload weight       
  W''_{floor} : 0.03497  Floor weight/area density                      
    W_{cargo} : 0.03148  Cargo weight                                   
  W''_{insul} : 0.02857  Weight/area density of insulation material     
   f_{string} : 0.02087  Fractional weight of stringers                 
   f_{lugg,2} : 0.01936  Proportion of passengers with two suitcases    
    p_{cabin} : 0.01785  Cabin air pressure (8,000ft)                   
    f_{frame} : 0.01491  Fractional frame weight                        
     f_{fadd} : 0.01193  Fractional added weight of local reinforcements
    T_{cabin} : -0.01785 Cabin temperature                              
            R : -0.01785 Universal gas constant                         
\sigma_{skin} : -0.1073  Max allowable skin stress                      
       c_{vt} : -0.8788  Vertical tail chord                            

