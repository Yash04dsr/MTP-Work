### Contents lists available at ScienceDirect

# International Journal of Hydrogen Energy

### journal homepage: http://www.elsevier.com/locate/he

## Comprehensive assessment of hydrogen injection in natural gas networks:

## Using dimensional analysis and reduced-order models for mixture quality

## prediction

## Carlos Montañés

#### ∗

## , Leyre Pardo, Jaime Milla-Val, Antonio Gómez

_Nabladot S.L., Salvador Allende 75, Zaragoza, 50015, Spain_

## A R T I C L E I N F O

_Keywords:_
Computational Fluid Dynamics (CFD)
Reduced-order modeling
Hydrogen injection
Natural gas pipelines
Gas mixture

## A B S T R A C T

#### This study presents a physics-based reduced-order model (ROM) to assess the mixing behavior of hydrogen

#### and natural gas in pipelines, facilitating the integration of hydrogen into natural gas networks—a key

#### strategy for reducing carbon emissions. The methodology consists of dimensional analysis to identify crucial

#### dimensionless parameters, CFD simulations for data collection, and statistical analysis for effective data

#### modeling. This approach enables rapid evaluation of injection strategies and operational conditions, reducing

#### the computational demands of traditional CFD simulations. The model correlates reduced-order parameters

#### with key dimensionless numbers like Reynolds number, and diameter and velocity ratios, to develop a

#### predictive tool for assessing mixture quality. Validated through extensive simulations, the model accurately

#### predicts gas mixing, using beta distributions for statistical representation to enhance data interpretability and

#### applicability.

### 1. Introduction

### Green hydrogen technologies have emerged as pivotal components

### in the contemporary energy landscape, spurred by the pressing need

### to combat climate change and curtail greenhouse gas emissions. Green

### hydrogen, with its climate neutrality, is a promising energy vector [1].

### It serves as an energy carrier for renewable energies and a solution

### for the storage of renewable energy [2]. Given these properties, the

### transport and distribution of hydrogen are widely researched and stud-

### ied to achieve an optimal integration of this resource into the energy

### mix [3–5].

### The most promising option for hydrogen distribution is the use

### of existing natural gas infrastructure, which is considered the most

### feasible solution in the short and medium term from both technical

### and economic perspectives [6,7]. Transportation of natural gas en-

### riched with hydrogen is currently the most efficient and cost-effective

### method [8]. However, the mixture of these two gases poses various

### challenges due to their different thermodynamic properties. These chal-

### lenges include concerns related to the integrity of pipe materials, safety

### issues, leaks, and the need to modify pipelines, storage tanks, com-

### pressors, and end-user devices [2,8–12]. Therefore, understanding the

### intricacies of hydrogen-natural gas mixtures is paramount, not only for

### safety considerations but also to optimize operational efficiency [13].

#### ∗Corresponding author.

#### E-mail address: carlos.montanes@nabladot.com (C. Montañés).

### A key process to mitigate the potential hazards that arise from the

### combined transportation of hydrogen and natural gas is the injection

### of hydrogen into natural gas pipelines [14]. Achieving a homogeneous

### mixture of hydrogen and natural gas in the shortest time is imperative

### to prevent the mentioned issues. Inadequate mixing of these gases can

### engender multifaceted risks: (i) elevated concentrations of hydrogen

### may catalyze degradation in the metallic infrastructure of natural gas

### pipelines [15–17]; and (ii) sub-optimal mixing can result in end-users

### receiving a blend with a higher-than-anticipated hydrogen content,

### potentially leading to operational challenges in utilizing the fuel [18–

### 20].

### For this reason, hydrogen injection into natural gas pipelines has

### been the subject of extensive research in scientific literature, using

### both experimental methods and computational fluid dynamics (CFD)

### to optimize the mixing process and avoid the potential issues indicated

### above. One example is the work of Zhou et al. [21], who developed

### dynamic models by numerically solving 1D partial differential equa-

### tions to simulate hydrogen injections in gas networks. Liu et al. [22]

### explored mixing dynamics using both experimental setups and CFD in a

### static mixer, offering a dual perspective on the phenomenon. Yan et al.

### [23] analyzed the influence of the hydrogen inlet configurations on

### mixing efficiency through CFD simulations. This work highlighted the

### critical role of structural variations in pipeline design. Concurrently, Su

#### https://doi.org/10.1016/j.ijhydene.2024.09.

#### Received 29 April 2024; Received in revised form 19 August 2024; Accepted 3 September 2024

#### International Journal of Hydrogen Energy 87 (2024) 442–

#### Available online 9 September 2024

#### 0360-3199/© 2024 Hydrogen Energy Publications LLC. Published by Elsevier Ltd. All rights are reserved, including those for text and data mining, AI training, and

#### similar technologies.


### et al. [24] utilized CFD to assess the quality of hydrogen-natural gas

### mixtures under various injection conditions. Furthermore, in this work

### a neural network model is developed to predict variations in H 2 concen-

### tration. Significant contributions also come from studies such as Eames

### et al. [14] and Khabbazi et al. [8], which examined the effects of T-

### junction orientation on mixing efficiency, and Smith et al. [25], which

### compared different turbulence models to determine the most accurate

### for predicting fluid behavior in T-junction configurations. Additionally,

### the dynamics of mixing in T-junctions, whether involving gases or

### hot and cold water, have been extensively studied, employing both

### experimental approaches and CFD techniques [26–29].

### This article presents a novel approach to design hydrogen injections

### into natural gas networks. The traditional approach consists of applying

### numerical fluid dynamic techniques (CFD) to design and optimize it.

### One of the main inconveniences of this approach is the time and

### cost required, as CFD techniques take several hours or even days to

### simulate a use case. The approach proposed involves creating a reduced

### physics model that can replicate the results of detailed numerical

### simulations in real-time. To achieve this, the authors have developed a

### methodology that combines traditional computational fluid dynamics

### (CFD) simulations with specific techniques of physics-based reduced-

### order models like dimensional and statistical analysis. This method

### produces a real-time model that can compute the hydrogen-natural gas

### mixture for a predefined geometric configuration, such as a T-junction.

### The model considers parameters like the flow ratio between the natural

### gas network and the hydrogen injection or the diameter ratio between

### the respective injection pipelines.

### While physics-based reduced-order models have been developed for

### other sectors, this approach is novel for H 2 injection. As a result, the

### outcome (a real-time model to simulate the H 2 injection) is particu-

### larly innovative. It has the potential to significantly reduce time and

### computational costs for the design of hydrogen injections into natural

### gas pipelines. Since the industry tends to develop standard solutions in

### which only a few parameters are allowed to vary, this model can be

### applied massively and impact the sector significantly.

### The integration of CFD and reduced-order models (ROMs) has be-

### come a powerful approach in engineering research to address the

### computational intensity of detailed simulations. This method involves

### using CFD simulations to generate detailed data sets, which then in-

### form the development of more computationally efficient ROMs through

### various techniques such as artificial intelligence, statistical methods, or

### simplified physical principles. For instance, König-Haagen et al. [30]

### successfully apply this strategy to develop ROMs for latent heat thermal

### energy storage systems, using data derived from CFD simulations.

### Similarly, Yang et al. [31] utilize proper orthogonal decomposition

### and Galerkin projection to create a ROM of a lead–bismuth reactor,

### demonstrating the effectiveness of this approach in simplifying complex

### thermal–hydraulic behaviors. Additionally, Li et al. [32] employ dimen-

### sional analysis in conjunction with CFD results to construct a predictive

### model for hydrogen dispersion in leakage scenarios, showcasing the

### versatility of ROMs in various application contexts.

### Further expanding ROM techniques, Zambrano et al. [33] explore

### tensor factorization for building surrogate models from sparse data,

### presenting an alternative to Gaussian process-based methods which

### often lack interpretability. This approach, implemented in the Twinkle

### library, effectively handles sparse data from CFD and FEM applications

### and is useful in both academic and industrial settings, especially for

### data analysis and post-processing. Using this library, García-Camprubí

### et al. [34] develop real-time virtual sensors for microfluidic processes,

### illustrating how ROMs can improve control systems in manufacturing,

### such as factory-on-chips, by predicting fluid dynamics that are difficult

### to measure directly.

### These examples highlight the growing trend of leveraging high-

### fidelity CFD simulations to underpin simpler, yet robust models that

### can significantly reduce computational demands while maintaining

### accuracy.

### The following section describes the methodology used to create the

### physics-based reduced-order model. After that, the results obtained are

### presented, and finally, we include the conclusions drawn from this

### work.

### 2. Methodologyandsetup

### As case study, our research employs a straightforward T-junction

### setup for hydrogen injection at the bottom of the primary pipeline,

### a configuration that has been extensively studied and validated in

### previous research. Eames et al. [14] and Khabbazi et al. [8] specifically

### demonstrated that lower injection points significantly enhance mixing

### by leveraging gravitational effects, compared to upper T-junction con-

### figurations which often result in poor mixing due to stratification. This

### result supported our decision to use the bottom injection approach, as

### it has been proven to optimize the mixing process. In this context, Su

### et al. [24] further explored the dynamics of hydrogen injection using

### CFD simulations to fine-tune the mixing efficiency.

### The objective of the methodology developed is to obtain a physics-

### based reduced-order model that can calculate the degree of mixing of

### hydrogen and natural gas in different sections downstream the injec-

### tion. The methodology consists of three stages: dimensional analysis,

### CFD simulation, and assessment of the mixture degree.

### Dimensional analysis allows the determination of dimensionless

### variables on which the degree of mixing depends, reducing the prob-

### lem’s dimensionality. This results in a considerable reduction of the

### CFD simulations required to obtain the dataset necessary to character-

### ize the hydrogen injection.

### The second stage consists of the configuration and execution of CFD

### simulations of the hydrogen injection into natural gas pipelines. The

### results of these simulations are processed to obtain the dataset that will

### feed the reduced-order model.

### The third stage consists of the elaboration of the reduced-order

### model and the adjustment of the mathematical expression that deter-

### mines the hydrogen degree of mixing downstream the injection.

### 2.1. Dimensionalanalysis

### A comprehensive exploration of all possible variable combinations

### involved in the injection process would require a huge amount of simu-

### lations, entailing significant computational resources and complicating

### the analysis of results. To mitigate these challenges, we have employed

### dimensional analysis to reduce the dimensionality of the problem. This

### approach serves as a cornerstone in the development of our reduced-

### order model by identifying key dimensionless parameters that condense

### the fundamental dynamics of the mixing process. This reduction not

### only aids in generalizing the solution across a wide range of conditions

### but also enhances the interpretability and applicability of the model.

### First, we introduce a dimensionless dependent variable, denoted

### as 𝑀 , which characterizes the degree of mixture in specific pipeline

### sections downstream the junction. While this variable will be defined

### in detail in the next section, we use it here generically to outline our

### methodological approach.

### The independent variables were initially defined as pipe diameters

### ( 𝑑 CH 4 , 𝑑 H 2 ), pressure ( 𝑃 ), temperature ( 𝑇 ), methane velocity ( 𝑣 CH 4 ),

### and mixture composition (%H 2 ):

### 𝑀 = 𝑓 ( 𝑑 CH 4 ,𝑑 H 2 ,𝑃,𝑇,𝑣 CH 4 , %H 2 ) (1)

### For mathematical convenience and to focus on the fundamental

### properties affecting fluid dynamics, we redefined the variables in terms

### of mixture gas density ( 𝜌 ), mixture gas viscosity ( 𝜇𝑔 ), and methane and

### hydrogen velocities ( 𝑣 CH 4 , 𝑣 H 2 ):

### 𝑀 = 𝑓 ′( 𝑑 CH 4 ,𝑑 H 2 ,𝜌,𝑣 CH 4 ,𝑣 H 2 ,𝜇𝑔 ) (2)

```
International Journal of Hydrogen Energy 87 (2024) 442–
```

```
Fig. 1. Representative geometry and mesh of the T-junction setup used in this study.
```
### Subsequently, we derived a dimensionless representation through

### dimensional analysis:

### 𝑀 = 𝐹

### (

### 𝑑 H 2

### 𝑑 CH 4

### ,

### 𝑣 H 2

### 𝑣 CH 4

### ,𝑅𝑒

### )

### (3)

### where 𝑅𝑒 denotes the Reynolds number, a fundamental dimension-

### less quantity in fluid mechanics, offering a well-established and inter-

### pretable measure of fluid flow characteristics.

### The choice of these particular dimensionless ratios (diameter and

### velocity ratios) provides clear insights into the mixing dynamics,

### thereby simplifying the complexity of the full-scale computational

### model into more tractable terms.

### This methodological approach enables an efficient assessment of the

### mixture quality across various parameter combinations. Using dimen-

### sional analysis, we mathematically reduced the number of variables

### from 6 dimensional ones to 3 dimensionless ones. Despite this reduc-

### tion, no physical information is lost in the process. This reduction

### significantly decreased the number of CFD simulations required to

### obtain the necessary dataset for characterizing hydrogen injection.

### Thus, by running a reduced number of simulations, primarily varying

### the Reynolds number, 𝑑 H 2 ∕ 𝑑 CH 4 , and 𝑣 H 2 ∕ 𝑣 CH 4 , we gained insights into

### how these parameters influence mixing behavior within the pipeline.

### 2.2. CFDsetup

### The CFD simulation setup follows to the methodologies described

### by Su et al. [24] and Eames et al. [14], which we adopt to generate

### the synthetic data necessary for developing our ROM. The Reynolds-

### averaged Navier–Stokes (RANS) equations are solved for continuity,

### momentum, energy, and species (H 2 ), assuming an ideal gas model.

### Turbulence within the system is modeled using the 𝑘 - 𝜔 SST model [35],

### selected for its proven accuracy in predicting flow behavior in com-

### plex geometries similar to our T-junction setup. Previous studies, such

### as Smith et al. [25], have highlighted the efficacy of this model in cap-

### turing essential dynamics in gas mixing scenarios, where phenomena

### like buoyancy play a significant role.

### While we used the described CFD setup, the methodology for ROM

### generation presented in this work can be applied to any CFD setup,

### allowing scalability with more advanced models (such as LES) as

### computational resources permit.

### The computational domain consists of a main pipe with a length

### of 10 m, with the T-junction placed ten diameters downstream the

### CH 4 entrance. The mesh includes 7.5 to 12 million polyhedral cells,

### varying with configuration, and it is refined near the walls to ensure

### that the wall-spacing parameter 𝑦 +remains approximately 1, reflecting

### a practice aligned with standards from referenced studies to ensure

### accuracy without conducting a separate mesh independence study. For

### better clarity of the T-junction setup and the injection scenarios tested

### in this work, a representative geometry and mesh are shown in Fig. 1.

### This investigation encompasses six distinct geometries, character-

### ized by the main pipe diameter, 𝑑 1 , ranging from 4 to 15 cm, and

### the hydrogen inlet pipe diameter, 𝑑 2 , varying from 1 to 3 cm. These

### variations result in 𝑑 2 ∕ 𝑑 1 ratios spanning from 0.1 to 0.6. Note that

### extreme cases such as1∕15or3∕4were not simulated; instead, the

### actual simulated extremes were1∕10and3∕5. Operational parameters

### were diversified to analyze a comprehensive range of scenarios. The

### velocity of natural gas, 𝑣 CH4, varied from 1 to 10 m/s, and the ratio of

### hydrogen to natural gas velocities, 𝑣 H 2 ∕ 𝑣 CH 4 , ranged from 2 to 150. The

### operating pressure fluctuated between 5 and 20 bar, with a consistent

### temperature of 27 ◦C. These conditions generated Reynolds numbers

### ranging from 7. 5 × 10^3 to 1. 18 × 10^6 , covering a spectrum of flow

### conditions for a thorough investigation. In total, 86 simulations were

### conducted, providing comprehensive coverage of the parameter space

### defined by the three dimensionless numbers illustrated in Fig. 2.

### 2.3. Reduced-ordermodelofmixturedegree

### Defining a ‘‘good’’ mixture is inherently subjective and can vary

### based on the specific application or system conditions. To establish an

### objective metric, we quantified the degree of mixture based on the mass

### fraction of H 2 within the pipeline. The challenge then becomes how to

### best represent these mass fraction statistically.

### While computational fluid dynamics (CFD) allows for the calcu-

### lation and visualization of mass fraction contours (Fig. 3 ), providing

### detailed spatial distributions, this approach often results in complex

### datasets. Although visualizing these contours offers comprehensive

### insights into the mixing process, comparing them across different cases

### can be cumbersome due to their complexity.

### To simplify the analysis, we moved from visualizing detailed con-

### tours to summarizing the data with histograms of mass fractions at

### various pipeline sections. These sections are defined by the dimen-

### sionless ratio 𝐿 ∕ 𝑑 CH 4 , where 𝐿 is the distance from the junction. This

### method not only makes the information easier to analyze but also

### helps compare mixing under different operational conditions. Fig. 4

### displays the histograms of mass fractions, showing the distribution of

### data points.

### Next, we computed Probability Density Functions (PDFs) from these

### histograms. We fit these PDFs to beta distribution functions for each

### section across all simulated cases. The beta distribution is particularly

### appropriate because it ranges from 0 to 1, matching the nature of

### mass fractions, and it can flexibly model the distribution shapes we

### observe in the CFD simulations. Fig. 5 shows the adjustment to a

### beta distribution, compared to the PDF computed using Kernel Density

### Estimation (KDE) [36], which smooths the discrete data points of the

### histogram into a continuous probability distribution, allowing us to

### directly assess the fit’s accuracy.

### The beta distribution can be parameterized using just two parame-

### ters, typically denoted as 𝛼 and 𝛽. Alternatively, it can be expressed in

### terms of 𝜇 (mean) and 𝜈 (sample size), which provide intuitively inter-

### pretable physical meanings. This parameterization helps in simplifying

### the representation of complex data and facilitates easier analysis and

### comparison of mixture quality across different conditions. The hydro-

### gen concentrations in each section were well represented by the beta

### distribution (see Fig. 5 ). Therefore, the next step involves obtaining

### a correlation based on previously defined dimensionless numbers to

### calculate the beta function parameters, 𝜇 and 𝜈. By obtaining a good

### correlation, we will be able to determine the mixture in the defined

### sections of the pipe downstream the injection.

```
International Journal of Hydrogen Energy 87 (2024) 442–
```

**Fig. 2.** Visualization of the parameter space exploration, where each point corresponds to a simulation and is characterized by the values of the three dimensionless numbers:
_𝑑_ H 2 ∕ _𝑑_ CH 4 , _𝑣_ H 2 ∕ _𝑣_ CH 4 , and _𝑅𝑒_. Dots colored with Reynolds number. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of
this article.)

```
Fig. 3. Contours of H 2 mass fraction in sections of a pipe for 𝐿 ∕ 𝑑 CH 4 equal to 2, 5, 10 and 50 (from left to right).
```
```
Fig. 4. Histogram of H 2 mass fraction (weighted with cross area) in sections of a pipe for 𝐿 ∕ 𝑑 CH 4 equal to 2, 5, 10 and 50 (from left to right).
```
```
Fig. 5. PDF and beta approximation for H 2 mass fraction in sections of a pipe for 𝐿 ∕ 𝑑 CH 4 equal to 2, 5, 10 and 50 (from left to right).
```
### The correlation established for the parameters 𝜇 andln( 𝜈 )takes

### the form of the mathematical expression defined in Eq. ( 4). Here, 𝜉

### represents the general form used to fit both 𝜇 andln( 𝜈 ). This means

### that 𝜉 can be replaced by either 𝜇 orln( 𝜈 )depending on the context,

### and the specific set of constants 𝐴 1 to 𝐷 6 will vary accordingly. Thus,

### these correlations only depend on the three dimensionless numbers

### determined for the problem ( 𝑁𝑑 = 𝑑 H 2 ∕ 𝑑 CH 4 , 𝑁𝑣 = 𝑣 H 2 ∕ 𝑣 CH 4 , and

### 𝑅𝑒 ). Given the disparity of absolute values for these numbers, for

### mathematical convenience, we use normalized values, defined as 𝜙̂ =

### 1 + ( 𝜙 − 𝜙 min)∕( 𝜙 max− 𝜙 min). The maximum and minimum values used

### for the normalization for each dimensionless number are defined in

### Table 1. The form of this expression was chosen because it is composed

### of simple terms, allowing us to analyze the specific influence of each

### variable. We tested different expressions of this type and found that

### this form provided a suitable balance between the number of terms and

### accuracy. While a simpler expression might suffice for 𝜇 , we used the

### same form for both parameters for consistency.

### The fitting of the parameters 𝐴 1 to 𝐷 6 in Eq. ( 4) was performed us-

## ing the curve_fit function from the scipy.optimize

### library [37]. This function employs non-linear least squares to fit the

```
International Journal of Hydrogen Energy 87 (2024) 442–
```

**Table 1**
Minimum and maximum values of dimensionless numbers used for normalization.

```
𝜙 min 𝜙 max
𝑁𝑑 0.1 0.
𝑁𝑣 1.0 150
Re 7459 1188750
```
## model to the data. Specifically,curve_fitadjusts the parameters

### to minimize the difference between the predicted values (from the

### mathematical expression) and the actual CFD results. This optimization

### process iteratively updates the parameters to find the best fit that

### reduces the error, ensuring that the model accurately represents the

### underlying data.

### While methods like neural networks might provide more accurate

### results with reasonable computational efficiency, this approach uses

### an algebraic expression that offers advantages in terms of ease of

### implementation. This model can be seamlessly integrated into various

### applications, including spreadsheets and other simple computational

### tools, making it highly accessible for engineers. The algebraic nature of

### the model allows for interpretation and quick calculations, facilitating

### real-time decision-making without the need for specialized software or

### extensive computational resources.

### 𝜉 = 𝐴 1 ln( 𝑁̂𝑣 ) + 𝐴 2 ln( 𝑅𝑒̂ ) + 𝐴 3 ln( 𝑁̂𝑑 )+

### 𝐴 4 𝑁̂𝑣 + 𝐴 5 𝑅𝑒̂ + 𝐴 6 𝑁̂𝑑 +

### 𝐴 7 𝑁̂𝑣

##### 2

### + 𝐴 8 𝑅𝑒̂

##### 2

### + 𝐴 9 𝑁̂𝑑

##### 2

### +

### 𝐴 10 𝑁̂𝑣

##### −

### + 𝐴 11 𝑅𝑒̂

##### −

### + 𝐴 12 𝑁̂𝑑

##### −

### +

### 𝐵 1 𝑁̂𝑣𝑅𝑒̂ + 𝐵 2 𝑁̂𝑣𝑁̂𝑑 + 𝐵 3 𝑅𝑒̂𝑁̂𝑑 +

### 𝐵 4 𝑁̂𝑣

(^2) _̂_

### 𝑅𝑒 + 𝐵 5 𝑁̂𝑣

(^2) _̂_

### 𝑁𝑑 + 𝐵 6 𝑅𝑒̂

(^2) _̂_

### 𝑁𝑣 +

### 𝐵 7 𝑅𝑒̂

(^2) _̂_

### 𝑁𝑑 + 𝐵 8 𝑁̂𝑑

(^2) _̂_

### 𝑁𝑣 + 𝐵 9 𝑁̂𝑑

(^2) _̂_

### 𝑅𝑒 +

### 𝐶 1 𝑁̂𝑣 ln( 𝑁̂𝑑 ) + 𝐶 2 𝑅𝑒̂ ln( 𝑁̂𝑑 ) + 𝐶 3 𝑁̂𝑑 ln( 𝑁̂𝑣 )+

### 𝐶 4 𝑅𝑒̂ ln( 𝑁̂𝑣 ) + 𝐶 5 𝑅𝑒̂ ln( 𝑅𝑒̂ ) + 𝐶 6 𝑁̂𝑑 ln( 𝑅𝑒̂ )+

### 𝐷 1 𝑅𝑒̂ exp( 𝑁̂𝑣 ) + 𝐷 2 𝑁̂𝑣 exp( 𝑅𝑒̂ ) + 𝐷 3 𝑁̂𝑣 exp( 𝑁̂𝑑 )+

### 𝐷 4 𝑁̂𝑑 exp( 𝑁̂𝑣 ) + 𝐷 5 𝑁̂𝑑 exp( 𝑅𝑒̂ ) + 𝐷 6 𝑅𝑒̂ exp( 𝑁̂𝑑 )

### (4)

### 3. Results

### This section details the results obtained from the comprehensive

### application of the developed methodology over 86 simulation cases,

### encompassing a wide range of operational scenarios. The primary

### outcome of this study is the establishment of a robust correlation model

### that predicts the mixture quality using the parameters 𝜇 andln( 𝜈 ),

### derived from dimensionless numbers.

### 3.1. Parameteroptimization

### Tables 2 and 3 present the optimized values for the parameters 𝐴 1 to

### 𝐷 6 in the correlation proposed for 𝜇 andln( 𝜈 ). The values are detailed

### for six dimensionless distances, 𝐿 ∕ 𝑑 CH 4 , downstream the T-junction,

### providing calculations that predict the evolution of the mixture up to

### a length equivalent to 50 diameters from the mixing point.

### 3.2. Validationofthecorrelation

### To assess the accuracy of our correlation, validation plots compare

### the true values with the predicted values for 𝜇 andln( 𝜈 ). Fig. 6 displays

### these plots, where different dot colors represent various values of the

### dimensionless length 𝐿 ∕ 𝑑 CH 4. The correlation coefficient R^2 for 𝜇 is

### 0.997, indicating an excellent fit, while forln( 𝜈 ), it is 0.945. As 𝐿 ∕ 𝑑 CH 4

### increases, the values of 𝜈 tend to rise, consistent with the inverse

### relationship to variance, reflecting an increase in mixture uniformity.

```
Table 2
Values of parameters 𝐴 1 to 𝐷 6 for the correlation equation for 𝜇 for different 𝐿 ∕ 𝑑 CH 4
values.
𝐿 ∕ 𝑑 CH 4 1 2 5 10 20 50
𝐴 1 −1.96E+ 3 −1.02E+ 3 −3.91E+ 2 −3.36E+ 2 −3.20E+ 2 −3.56E+ 2
𝐴 2 3.84E+2 2.86E+2 1.51E+2 1.97E+2 2.24E+2 2.28E+ 2
𝐴 3 −1.60E+ 2 −1.82E+ 2 −1.13E+ 2 −6.79E+ 1 −7.74E+ 1 −6.05E+ 1
𝐴 4 1.57E+3 8.36E+2 3.79E+2 3.22E+2 2.97E+2 3.22E+ 2
𝐴 5 −1.09E+ 3 −6.73E+ 2 −3.56E+ 2 −3.50E+ 2 −3.59E+ 2 −3.75E+ 2
𝐴 6 2.12E+2 2.51E+2 1.94E+2 1.80E+2 1.97E+2 1.92E+ 2
𝐴 7 −2.24E+ 2 −1.29E+ 2 −6.16E+ 1 −5.33E+ 1 −5.07E+ 1 −5.41E+ 1
𝐴 8 −9.01E+ 1 −5.18E+ 1 −3.23E+ 1 −1.51E+ 1 −8.28E+ 0 −8.32E+ 0
𝐴 9 −8.31E+ 0 −1.12E+ 1 −6.59E+ 0 −3.77E+ 0 −4.21E+ 0 −2.60E+ 0
𝐴 10 −7.75E+ 2 −3.79E+ 2 −1.21E+ 2 −1.03E+ 2 −9.62E+ 1 −1.11E+ 2
𝐴 11 5.89E+1 5.80E+1 3.16E+1 5.74E+1 7.11E+1 7.19E+ 1
𝐴 12 −8.54E+ 1 −9.18E+ 1 −5.77E+ 1 −3.42E+ 1 −3.94E+ 1 −3.21E+ 1
𝐵 1 4.70E+2 2.41E+2 9.64E+1 1.03E+2 1.06E+2 1.24E+ 2
𝐵 2 −8.80E+ 1 −8.94E+ 1 −1.25E+ 2 −1.23E+ 2 −1.17E+ 2 −1.23E+ 2
𝐵 3 4.29E+1 2.06E+1 3.66E+ 1 −6.29E− 1 −1.51E+ 1 −2.16E+ 1
𝐵 4 −2.23E+ 2 −1.26E+ 2 −5.90E+ 1 −5.73E+ 1 −5.70E+ 1 −6.34E+ 1
𝐵 5 5.46E+1 5.30E+1 4.54E+1 4.56E+1 4.63E+1 4.87E+ 1
𝐵 6 1.15E+1 8.36E+0 8.00E+0 8.53E+0 6.29E+0 4.65E+ 0
𝐵 7 −2.64E+ 1 −1.30E+ 1 −1.03E+ 1 −3.53E+0 2.16E+0 3.60E+ 0
𝐵 8 −2.62E+ 1 −2.42E+ 1 −5.89E+ 0 −7.80E+ 0 −1.07E+ 1 −1.13E+ 1
𝐵 9 −2.81E+ 0 −3.59E+ 0 −1.14E+ 1 −2.90E+ 0 −7.35E−1 1.29E+ 0
𝐶 1 −4.62E+ 1 −4.30E+ 1 −1.29E+ 1 −1.48E+ 1 −1.97E+ 1 −2.07E+ 1
𝐶 2 −1.54E+ 1 −1.21E+ 1 −2.18E+ 1 −6.16E+ 0 −3.26E+ 0 −4.06E− 1
𝐶 3 9.95E+1 9.90E+1 9.14E+1 9.33E+1 9.49E+1 9.92E+ 1
𝐶 4 −2.54E+ 2 −1.31E+ 2 −5.41E+ 1 −5.95E+ 1 −5.97E+ 1 −6.79E+ 1
𝐶 5 4.53E+2 2.79E+2 1.56E+2 1.16E+2 1.03E+2 1.07E+ 2
𝐶 6 −4.97E+0 2.60E+0 3.31E+0 8.16E+0 1.22E+1 1.24E+ 1
𝐷 1 8.05E+1 4.86E+1 2.49E+1 2.30E+1 2.25E+1 2.44E+ 1
𝐷 2 −5.06E+ 0 −3.61E+ 0 −3.48E+ 0 −3.78E+ 0 −2.78E+ 0 −2.09E+ 0
𝐷 3 6.44E+0 5.77E+0 7.94E−1 1.45E+0 2.21E+0 2.35E+ 0
𝐷 4 −1.36E+ 1 −1.32E+ 1 −1.09E+ 1 −1.09E+ 1 −1.10E+ 1 −1.16E+ 1
𝐷 5 1.36E+1 7.72E+0 6.38E+0 3.49E+0 1.12E+0 4.25E− 1
𝐷 6 −3.98E−1 3.58E−1 2.84E+0 7.50E−1 7.19E− 2 −5.37E− 1
```
### Interestingly, the dispersion ofln( 𝜈 )values also increases with

### higher 𝐿 ∕ 𝑑 CH 4 , ranging from an R^2 of 0.97 at 𝐿 ∕ 𝑑 CH 4 = 1to 0.82 at

### 𝐿 ∕ 𝑑 CH 4 = 50. This pattern suggests more nuanced dynamics as the gas

### travels further from the injection point. One possible explanation for

### this behavior is the exponentially higher values of 𝜈 , which suggest

### a distribution increasingly resembling a delta function. This implies

### greater uncertainty in the method at these points, potentially due to

### the higher homogeneity of the mixture, which paradoxically makes the

### precise characterization of mixture quality less critical at these stages

### due to better overall mixing. Such observations highlight the complex

### interplay between mixing efficiency and measurement certainty, un-

### derscoring the need for careful interpretation of model predictions in

### varied operational contexts.

### 3.3. Interpretationofcorrelationresults

### Fig. 7 offers a colormap representation of the correlation results

### ( 𝜇 andln( 𝜈 )) in a 2D space defined by the dimensionless numbers

### 𝑁𝑑 = 𝑑 H 2 ∕ 𝑑 CH 4 and 𝑁𝑣 = 𝑣 H 2 ∕ 𝑣 CH 4. The visual analysis shows smooth

### transitions in the function values across the parameter space, indicating

### a stable and consistent model behavior under varying conditions. These

### smooth gradients, while visually simplistic, underscore the capacity of

### the model to handle complex real-world scenarios without resorting to

### overly intricate or erratic solutions. Such stability in the model’s pre-

### dictions across diverse conditions is a strong indicator of its robustness

### and reliability.

### To aid in interpreting the Figure, we included iso-lines of con-

### stant hydrogen blend ratio (HBR, a commonly used metric in this

### context [17,24,38–42] ) values. The relationship between HBR and the

### dimensionless numbers is given by 𝑁𝑑^2 𝑁𝑣 =HBR∕(1 −HBR). Including

### these iso-lines helps in visualizing how the dimensionless parameters

### relate to practical HBR values, enhancing the interpretability of the

### figure.

```
International Journal of Hydrogen Energy 87 (2024) 442–
```

**Fig. 6.** Validation plots comparing true values with correlated values for _𝜇_ (left) andln( _𝜈_ )(right). Different dot colors represent various values of the dimensionless length _𝐿_ ∕ _𝑑_ CH 4.
(For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)

**Fig. 7.** Contours of correlated values of _𝜇_ (left) andln( _𝜈_ )(right) for constant Re= 105 and _𝐿_ ∕ _𝑑_ CH 4 = 2, for the range studied of _𝑁𝑑_ and _𝑁𝑣_. The dots (colored with Reynolds
number) indicate the simulations in the phase space. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)

### 4. Computationaldetails

### The CFD simulations were performed using Ansys Fluent. Each case

### required approximately 100 CPU-hours, consumed around 20 GB of

### RAM and used 2 Gb of storage for each case. The simulations were

### executed on an AMD Ryzen 5900X processor.

### The post-processing of CFD-generated data, including the genera-

### tion of histograms, PDFs, fitting to beta distribution functions, and

### parameter optimization for the tables Tables 2 and 3 , took about 10 min

### of computational time.

### The evaluation of the parameters using the algebraic expression

### and the reconstruction of the beta function are nearly instantaneous,

### demonstrating the efficiency of the ROM approach compared to the full

### CFD simulations.

### 5. Conclusions

### This study has developed and validated a novel reduced-order

### model to assess the mixing quality of hydrogen in natural gas pipelines,

### utilizing dimensional analysis and computational fluid dynamics (CFD).

### By leveraging advanced simulation techniques and statistical analy-

### sis, the research provides a robust framework for predicting mixture

### behavior under various operational conditions.

### The proposed model demonstrated high predictive accuracy, as

### evidenced by the correlation coefficients (R^2 ) close to 1 for parameter

### 𝜇 and satisfactorily high forln( 𝜈 ). This high level of accuracy indi-

### cates that the model is not only robust but also reliable for practical

### applications in the field of gas transportation and distribution. The

### use of dimensional analysis significantly reduced the computational

### complexity involved in the simulations, making the study more ef-

### ficient. Focusing on key dimensionless numbers allowed the model

### to capture essential mixing dynamics without the need for extensive

### computational resources.

### The integration of beta distribution functions to analyze mass frac-

### tion data further highlighted the ability of the model to handle complex

### data sets and provide meaningful insights into the mixing processes.

### These statistical tools helped simplify the data analysis, allowing for

### clearer interpretations of the mixing quality across different pipeline

### sections.

### The successful application of the developed methodology and its

### validation suggest its potential for broader applications. Future work

### will aim to expand the range of simulation scenarios, potentially incor-

### porating more diverse geometrical and operational conditions to fur-

### ther validate and refine the model. Additionally, exploring alternative

### algebraic expressions through symbolic regression, such as PySR [43],

### could offer new insights and enhance model predictability. While not

### explicitly analyzed in this paper, such enhancements could serve to

### address any unexplored dynamics or to improve the precision of the

### model predictions in future iterations.

```
International Journal of Hydrogen Energy 87 (2024) 442–
```

**Table 3**
Values of parameters _𝐴_ 1 to _𝐷_ 6 for the correlation equation forln( _𝜈_ )for different _𝐿_ ∕ _𝑑_ CH 4
values.
_𝐿_ ∕ _𝑑_ CH 4 1 2 5 10 20 50
_𝐴_ 1 −7.50E+ 3 −1.68E+ 4 −2.90E+ 4 −3.41E+ 4 −3.24E+ 4 −5.02E+ 4
_𝐴_ 2 1.19E+3 2.15E+ 3 −2.29E+ 3 −1.10E+ 4 −1.39E+ 4 −1.09E+ 4
_𝐴_ 3 3.07E+3 5.11E+3 9.75E+3 9.75E+3 1.19E+4 1.55E+ 4
_𝐴_ 4 6.39E+3 1.43E+4 2.51E+4 3.09E+4 2.86E+4 4.24E+ 4
_𝐴_ 5 −4.78E+ 3 −8.05E+ 3 −9.63E+ 3 −6.64E+ 3 −7.47E+ 2 −5.43E+ 3
_𝐴_ 6 1.01E+2 3.69E+ 2 −8.30E+ 2 −1.20E+ 3 −2.25E+ 3 −6.49E+ 3
_𝐴_ 7 −9.36E+ 2 −2.38E+ 3 −4.07E+ 3 −5.04E+ 3 −4.97E+ 3 −6.64E+ 3
_𝐴_ 8 −2.61E+ 2 −1.36E+ 3 −3.77E+ 3 −6.25E+ 3 −7.21E+ 3 −7.91E+ 3
_𝐴_ 9 2.24E+2 4.48E+2 8.79E+2 9.30E+2 1.03E+3 1.25E+ 3
_𝐴_ 10 −2.65E+ 3 −5.65E+ 3 −9.72E+ 3 −1.08E+ 4 −9.70E+ 3 −1.73E+ 4
_𝐴_ 11 −6.84E+ 0 −2.11E+ 2 −2.86E+ 3 −7.48E+ 3 −8.60E+ 3 −7.84E+ 3
_𝐴_ 12 1.51E+3 2.26E+3 4.17E+3 3.97E+3 5.18E+3 7.14E+ 3
_𝐵_ 1 3.77E+3 5.16E+3 8.02E+3 7.77E+3 5.51E+3 7.03E+ 3
_𝐵_ 2 −2.31E+ 3 −3.01E+ 3 −5.98E+ 3 −8.38E+ 3 −6.41E+ 3 −3.98E+ 3
_𝐵_ 3 −1.19E+ 3 −2.69E+ 3 −3.05E+ 3 −1.50E+ 2 −3.30E+ 3 −5.24E+ 3
_𝐵_ 4 −1.54E+ 3 −2.65E+ 3 −4.26E+ 3 −4.68E+ 3 −3.88E+ 3 −4.57E+ 3
_𝐵_ 5 7.47E+2 1.44E+3 2.46E+3 3.12E+3 2.76E+3 1.63E+ 3
_𝐵_ 6 −1.86E+ 2 −2.98E+ 2 −7.09E+ 2 −1.14E+ 3 −1.73E+ 3 −2.07E+ 3
_𝐵_ 7 8.86E+1 4.69E+ 1 −2.97E+ 2 −1.15E+ 3 −7.20E+ 2 −3.98E+ 2
_𝐵_ 8 −4.18E+ 1 −4.58E+ 2 −4.66E+ 2 −2.72E+ 2 −6.31E+ 2 −4.41E+ 2
_𝐵_ 9 4.07E+2 8.76E+2 1.17E+3 8.87E+2 1.51E+3 1.81E+ 3
_𝐶_ 1 −2.86E+ 1 −8.15E+ 2 −8.85E+ 2 −6.56E+ 2 −1.18E+ 3 −6.76E+ 2
_𝐶_ 2 7.49E+2 1.36E+3 1.57E+3 9.17E+2 2.11E+3 2.82E+ 3
_𝐶_ 3 1.41E+3 2.55E+3 4.33E+3 5.43E+3 4.84E+3 3.05E+ 3
_𝐶_ 4 −1.87E+ 3 −2.38E+ 3 −3.49E+ 3 −2.79E+ 3 −1.04E+ 3 −1.58E+ 3
_𝐶_ 5 1.79E+3 5.52E+3 1.15E+4 1.68E+4 1.87E+4 2.22E+ 4
_𝐶_ 6 −5.86E+1 1.49E+2 7.10E+ 1 −9.44E+ 2 −2.84E+2 2.46E+ 2
_𝐷_ 1 4.98E+2 1.03E+3 1.70E+3 2.01E+3 1.83E+3 2.07E+ 3
_𝐷_ 2 8.20E+1 1.42E+2 3.48E+2 5.47E+2 8.18E+2 9.78E+ 2
_𝐷_ 3 1.62E+1 1.17E+2 1.14E+2 5.51E+1 1.61E+2 1.26E+ 2
_𝐷_ 4 −1.78E+ 2 −3.60E+ 2 −6.25E+ 2 −7.96E+ 2 −7.01E+ 2 −3.91E+ 2
_𝐷_ 5 −6.95E+1 3.88E+0 2.06E+2 5.09E+2 3.81E+2 2.72E+ 2
_𝐷_ 6 −1.03E+ 2 −2.42E+ 2 −3.40E+ 2 −2.80E+ 2 −4.32E+ 2 −4.98E+ 2

### This research contributes significantly to the field by offering a prac-

### tical yet sophisticated approach to modeling gas mixtures in pipeline

### networks, which is crucial for the ongoing integration of hydrogen into

### existing natural gas infrastructures as part of broader energy transition

### efforts.

### CRediTauthorshipcontributionstatement

### Carlos Montañés: Conceptualization, Methodology, Supervision,

### Writing – original draft, Writing – review & editing. Leyre Pardo:

### Investigation, Data curation, Writing – original draft. JaimeMilla-Val:

### Formal analysis, Data curation. Antonio Gómez: Project administra-

### tion, Writing – review & editing.

### Declarationofcompetinginterest

### The authors declare that they have no known competing finan-

### cial interests or personal relationships that could have appeared to

### influence the work reported in this paper.

### Declaration of Generative AI and AI-assisted technologies in the

### writingprocess

### During the preparation of this work the authors used ChatGPT to

### improve the readability of the text. The authors reviewed any suggested

### wording and edited it as needed; they take full responsibility for the

### content of the publication.

### Acknowledgments

### This project has received funding from Smart Energy Systems ERA-

### Net program - EnerDigit call with co-financing from CDTI (Spanish

### Center for the Industrial Technological Development) and the Research

### and Innovation Framework Program ≪ Horizon 2020 ≫ of the European

### Union.

### References

```
[1] Kovač A, Paranos M, Marciuš D. Hydrogen in energy transition: A review. Int
J Hydrog Energy 2021;46:10016–35. http://dx.doi.org/10.1016/j.ijhydene.2020.
11.256, Hydrogen and Fuel Cells.
[2] Fernandes LA, Marcon LRC, Rouboa A. Simulation of flow conditions for natural
gas and hydrogen blends in the distribution natural gas network. Int J Hydrog
Energy 2024;59:199–213. http://dx.doi.org/10.1016/j.ijhydene.2024.01.014.
[3] Lehner M, Tichler R, Steinmüller H, Koppe M, et al. Power-to-gas: Technology
and business models. Springer; 2014.
[4] Wang A. European hydrogen backbone: How a dedicated hydrogen infrastructure
can be created. 2020.
[5] Villuendas T, Montañés C, Gómez A, Alarcón AC, Storch de Gracia MD, Sánchez-
Laínez J. Advancing in the decarbonized future of natural gas transmission
networks through a CFD study. Int J Hydrog Energy 2022;47:15832–44. http:
//dx.doi.org/10.1016/j.ijhydene.2022.03.055.
[6] Gondal IA. Hydrogen integration in power-to-gas networks. Int J Hydrog Energy
2019;44:1803–15. http://dx.doi.org/10.1016/j.ijhydene.2018.11.164.
[7] Erdener BC, Sergi B, Guerra OJ, Lazaro Chueca A, Pambour K, Brancucci C, et al.
A review of technical and regulatory limits for hydrogen blending in natural gas
pipelines. Int J Hydrog Energy 2023;48:5595–617. http://dx.doi.org/10.1016/j.
ijhydene.2022.10.254.
[8] Khabbazi AJ, Zabihi M, Li R, Hill M, Chou V, Quinn J. Mixing hydrogen into
natural gas distribution pipeline system through tee junctions. Int J Hydrog
Energy 2024;49:1332–44. http://dx.doi.org/10.1016/j.ijhydene.2023.11.038.
[9] Sánchez-Laínez J, Cerezo A, Storch de Gracia MD, Aragón J, Fernandez E,
Madina V, et al. Enabling the injection of hydrogen in high-pressure gas grids:
Investigation of the impact on materials and equipment. Int J Hydrog Energy
2024;52:1007–18. http://dx.doi.org/10.1016/j.ijhydene.2023.05.220.
[10] Tian X, Pei J. Study progress on the pipeline transportation safety of
hydrogen-blended natural gas. Heliyon 2023;9:e21454. http://dx.doi.org/10.
1016/j.heliyon.2023.e21454.
[11] labidine Messaoudani Z, Rigas F, Hamid MDB, Hassan CRC. Hazards, safety and
knowledge gaps on hydrogen transmission via natural gas grid: A critical review.
Int J Hydrog Energy 2016;41:17511–25.
[12] Abd AA, Naji SZ, Thian TC, Othman MR. Evaluation of hydrogen concentration
effect on the natural gas properties and flow performance. Int J Hydrog Energy
2021;46:974–83. http://dx.doi.org/10.1016/j.ijhydene.2020.09.141.
[13] Mahajan D, Tan K, Venkatesh T, Kileti P, Clayton CR. Hydrogen blending in gas
pipeline networks — A review. Energies 2022;15. http://dx.doi.org/10.3390/
en15103582.
[14] Eames I, Austin M, Wojcik A. Injection of gaseous hydrogen into a natural gas
pipeline. Int J Hydrog Energy 2022;47:25745–54. http://dx.doi.org/10.1016/j.
ijhydene.2022.05.300.
[15] Briottet L, Moro I, Lemoine P. Quantifying the hydrogen embrittlement of
pipeline steels for safety considerations. Int J Hydrog Energy 2012;37:17616–23.
http://dx.doi.org/10.1016/j.ijhydene.2012.05.143, HySafe 1.
[16] Capelle J, Gilgert J, Dmytrakh I, Pluvinage G. Sensitivity of pipelines with steel
API X52 to hydrogen embrittlement. Int J Hydrog Energy 2008;33:7630–41.
http://dx.doi.org/10.1016/j.ijhydene.2008.09.020.
[17] Zhao W, Wang W, Li S, Li X, Sun C, Sun J, et al. Insights into the role of CO
in inhibiting hydrogen embrittlement of X80 steel weld at different hydrogen
blending ratios. Int J Hydrog Energy 2024;50:292–302. http://dx.doi.org/10.
1016/j.ijhydene.2023.10.167.
[18] Leicher J, Schaffert J, Cigarida H, Tali E, Burmeister F, Giese A, et al. The
impact of hydrogen admixture into natural gas on residential and commercial
gas appliances. Energies 2022;15. http://dx.doi.org/10.3390/en15030777.
[19] Middha P, Engel D, Hansen OR. Can the addition of hydrogen to natural gas
reduce the explosion risk? Int J Hydrog Energy 2011;36:2628–36. http://dx.doi.
org/10.1016/j.ijhydene.2010.04.132, The Third Annual International Conference
on Hydrogen Safety.
[20] Shirvill LC, Roberts TA, Royle M, Willoughby DB, Sathiah P. Experimental study
of hydrogen explosion in repeated pipe congestion — Part 2: Effects of increase
in hydrogen concentration in hydrogen-methane-air mixture. Int J Hydrog Energy
2019;44:3264–76. http://dx.doi.org/10.1016/j.ijhydene.2018.12.021.
[21] Zhou D, Wang C, Yan S, Yan Y, Guo Y, Shao T, et al. Dynamic modeling
and characteristic analysis of natural gas network with hydrogen injections. Int
J Hydrog Energy 2022;47:33209–23. http://dx.doi.org/10.1016/j.ijhydene.2022.
07.246.
[22] Liu Y, Rao A, Ma F, Li X, Wang J, Xiao Q. Investigation on mixing characteristics
of hydrogen and natural gas fuel based on SMX static mixer. Chem Eng Res Des
2023;197:738–49. http://dx.doi.org/10.1016/j.cherd.2023.07.040.
[23] Yan S, Jia G, Xu W, Li R, Lu Y, Cai M. Computational fluid dynamic analysis
of hydrogen-injected natural gas for mixing and transportation behaviors in
pipeline structures. Energy Sci Eng 2023;11:2912–28. http://dx.doi.org/10.1002/
ese3.1500.
[24] Su Y, Li J, Guo W, Zhao Y, Li J, Zhao J, et al. Prediction of mixing uniformity
of hydrogen injection in natural gas pipeline based on a deep learning model.
Energies 2022;15. http://dx.doi.org/10.3390/en15228694.
```
```
International Journal of Hydrogen Energy 87 (2024) 442–
```

[25] Smith BL, Mahaffy JH, Angele K. A CFD benchmarking exercise based on flow
mixing in a T-junction. Nucl Eng Des 2013;264:80–8. [http://dx.doi.org/10.1016/](http://dx.doi.org/10.1016/)
j.nucengdes.2013.02.030, SI:NURETH-14.
[26] Kok JBW, van der Wal S. Mixing in T-junctions. Appl Math Model
1996;20:232–43. [http://dx.doi.org/10.1016/0307-904X(95)00151-9.](http://dx.doi.org/10.1016/0307-904X(95)00151-9.)
[27] Kickhofel J, Prasser H-M, Selvam PK, Laurien E, Kulenovic R. T-junction
cross-flow mixing with thermally driven density stratification. Nucl Eng Des
2016;309:23–39. [http://dx.doi.org/10.1016/j.nucengdes.2016.08.039.](http://dx.doi.org/10.1016/j.nucengdes.2016.08.039.)
[28] Evrim C, Chu X, Laurien E. Analysis of thermal mixing characteristics in
different T-junction configurations. Int J Heat Mass Transfer 2020;158:120019.
[http://dx.doi.org/10.1016/j.ijheatmasstransfer.2020.120019.](http://dx.doi.org/10.1016/j.ijheatmasstransfer.2020.120019.)
[29] Ayhan H, Sökmen CN. CFD modeling of thermal mixing in a T-junction geometry
using LES model. Nucl Eng Des 2012;253:183–91. [http://dx.doi.org/10.1016/j.](http://dx.doi.org/10.1016/j.)
nucengdes.2012.08.010, SI : CFD4NRS-3.
[30] König-Haagen A, Faden M, Diarce G. A CFD results-based reduced-order model
for latent heat thermal energy storage systems with macro-encapsulated PCM. J
Energy Storage 2023;73:109235. [http://dx.doi.org/10.1016/j.est.2023.109235.](http://dx.doi.org/10.1016/j.est.2023.109235.)
[31] Yang T, Zhao P, Zhao Y, Yu T. Development of reduced-order thermal stratifica-
tion model for upper plenum of a lead–bismuth fast reactor based on CFD. Nucl
Eng Technol 2023;55:2835–43. [http://dx.doi.org/10.1016/j.net.2023.05.002.](http://dx.doi.org/10.1016/j.net.2023.05.002.)
[32] Li Z, Simancas NSN, Vianna SSV, Zhang B. A mathematical model for hydrogen
dispersion cloud based on dimensional analysis and computational fluid dynam-
ics (CFD). Int J Hydrog Energy 2024;60:229–40. [http://dx.doi.org/10.1016/j.](http://dx.doi.org/10.1016/j.)
ijhydene.2024.02.119.
[33] Zambrano V, Rodríguez-Barrachina R, Calvo S, Izquierdo S. TWINKLE: A
digital-twin-building kernel for real-time computer-aided engineering. SoftwareX
2020;11:100419. [http://dx.doi.org/10.1016/j.softx.2020.100419.](http://dx.doi.org/10.1016/j.softx.2020.100419.)
[34] García-Camprubí M, Bengoechea-Cuadrado C, Izquierdo S. Virtual sensor
development for continuous microfluidic processes. IEEE Trans Ind Inf
2020;16:7774–81. [http://dx.doi.org/10.1109/TII.2020.2972111.](http://dx.doi.org/10.1109/TII.2020.2972111.)

```
[35] Menter FR. Two-equation eddy-viscosity turbulence models for engineering
applications. AIAA J 1994;32:1598–605. http://dx.doi.org/10.2514/3.12149.
[36] Rosenblatt M. Remarks on some nonparametric estimates of a density function.
Ann Math Stat 1956;27:832–7. http://dx.doi.org/10.1214/aoms/1177728190.
[37] Virtanen P, Gommers R, Oliphant TE, Haberland M, Reddy T, Cournapeau D, et
al. SciPy 1.0: Fundamental algorithms for scientific computing in Python. Nature
Methods 2020;17:261–72. http://dx.doi.org/10.1038/s41592-019-0686-2.
[38] Yang K, Li W, Dai X, Guo Y, Pang L. Effect of hydrogen ratio on leakage and
explosion characteristics of hydrogen-blended natural gas in utility tunnels. Int J
Hydrog Energy 2024;64:132–47. http://dx.doi.org/10.1016/j.ijhydene.2024.03.
247.
[39] Xu S, Chen Y, Tian Z, Liu H. NO emission reduction characteristics of CH4/H
staged MILD combustion over a wide range of hydrogen-blending ratios. Fuel
2024;372:132239. http://dx.doi.org/10.1016/j.fuel.2024.132239.
[40] Yu X, Li Y, Zhang J, Guo Z, Du Y, Li D, et al. Effects of hydrogen blending ratio
on combustion and emission characteristics of an ammonia/hydrogen compound
injection engine under different excess air coefficients. Int J Hydrog Energy
2024;49:1033–47. http://dx.doi.org/10.1016/j.ijhydene.2023.10.049.
[41] Wang C, Wang H, Ji X, Xu H, Yang C, Meng X. Hybrid energy storage capacity
configuration strategy for virtual power plants based on variable-ratio natural
gas-hydrogen blending. Int J Hydrog Energy 2024;58:433–45. http://dx.doi.org/
10.1016/j.ijhydene.2024.01.175.
[42] Dong H, Li R, Zhao W, Zhang Y, Chen X, Zhang Q, et al. Chemical kinetics
properties and the influences of different hydrogen blending ratios on reactions of
natural gas. Case Stud Therm Eng 2023;41:102676. http://dx.doi.org/10.1016/
j.csite.2022.102676.
[43] Cranmer M. Interpretable machine learning for science with PySR and
SymbolicRegression.jl. 2023, arXiv:2305.01582.
```
```
International Journal of Hydrogen Energy 87 (2024) 442–
```

